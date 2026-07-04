import time
import asyncio
from typing import Any, Dict
from app.database.connection import AsyncSessionLocal
from app.repositories.conversation_repo import ConversationRepository

class LeadStateManager:
    def __init__(self, lead_id: int | None):
        self.lead_id = lead_id
        # Schema: { field_name: {"status": "UNKNOWN" | "KNOWN" | "DECLINED" | "INFERRED", "value": Any} }
        self.state: Dict[str, Dict[str, Any]] = {
            "name": {"status": "UNKNOWN", "value": None},
            "email": {"status": "UNKNOWN", "value": None},
            "phone": {"status": "UNKNOWN", "value": None},
            "company": {"status": "UNKNOWN", "value": None},
            "industry": {"status": "UNKNOWN", "value": None},
            "requirement": {"status": "UNKNOWN", "value": None},
            "monthly_leads": {"status": "UNKNOWN", "value": None},
            "company_size": {"status": "UNKNOWN", "value": None},
            "budget": {"status": "UNKNOWN", "value": None},
            "timeline": {"status": "UNKNOWN", "value": None},
            "decision_maker": {"status": "UNKNOWN", "value": None},
        }
        self.uncommitted_changes = 0
        self.last_update_time = time.time()
        self._lock = asyncio.Lock()

    async def load_from_db(self):
        if not self.lead_id:
            return
        async with AsyncSessionLocal() as session:
            repo = ConversationRepository(session)
            profile = await repo.get_lead_profile(self.lead_id)
            if not profile:
                return
            for key in self.state.keys():
                val = profile.get(key)
                if val:
                    self.state[key]["status"] = "KNOWN"
                    self.state[key]["value"] = val
        self.uncommitted_changes = 0

    def update_extracted_info(self, extracted_data: Dict[str, Any]):
        """
        Takes raw extracted info from the LLM and applies business logic to determine
        the state transitions.
        """
        fields = ["name", "email", "phone", "company", "industry", "requirement", "monthly_leads", "company_size", "budget", "timeline", "decision_maker"]
        declined_reasons = ["declined", "refused", "won't share", "not sharing", "user declined", "not applicable"]
        
        for field in fields:
            if field in extracted_data:
                val = extracted_data[field]
                reason = str(extracted_data.get(f"{field}_reason", "")).lower()
                
                # Check if declined
                is_declined = any(d in reason for d in declined_reasons) or (isinstance(val, str) and any(d in val.lower() for d in declined_reasons))
                
                if is_declined:
                    self.state[field]["status"] = "DECLINED"
                    self.state[field]["value"] = None
                    self.uncommitted_changes += 1
                elif val is not None and val != "":
                    # Transition to KNOWN or INFERRED
                    # (For simplicity, we'll mark as KNOWN if it's explicitly provided)
                    self.state[field]["status"] = "KNOWN"
                    self.state[field]["value"] = val
                    self.uncommitted_changes += 1
                    
        self.last_update_time = time.time()

    async def commit(self):
        """Perform a single batched database update."""
        if not self.lead_id or self.uncommitted_changes == 0:
            return
            
        async with self._lock:
            # Double check inside lock
            if self.uncommitted_changes == 0:
                return
                
            update_payload = {}
            for field, data in self.state.items():
                if data["status"] in ["KNOWN", "INFERRED"] and data["value"] is not None:
                    update_payload[field] = data["value"]
            
            if update_payload:
                try:
                    async with AsyncSessionLocal() as session:
                        repo = ConversationRepository(session)
                        await repo.update_lead(self.lead_id, update_payload)
                    print(f">>> LeadStateManager committed {self.uncommitted_changes} changes for lead {self.lead_id}")
                except Exception as e:
                    print(f">>> DB commit failed: {e}")
                    return
            
            self.uncommitted_changes = 0
            self.last_update_time = time.time()

    def get_prompt_context(self) -> str:
        """Returns the dynamically formatted state string for LLM injection."""
        known = []
        missing = []
        declined = []
        
        for field, data in self.state.items():
            if data["status"] in ["KNOWN", "INFERRED"]:
                known.append(f"{field}: {data['value']}")
            elif data["status"] == "DECLINED":
                declined.append(field)
            else:
                missing.append(field)
                
        context = "CURRENT LEAD STATE:\n"
        context += "Known Fields:\n" + ("\n".join(f"- {k}" for k in known) if known else "- None") + "\n\n"
        context += "Missing Fields:\n" + ("\n".join(f"- {m}" for m in missing) if missing else "- None") + "\n\n"
        context += "Declined Fields:\n" + ("\n".join(f"- {d}" for d in declined) if declined else "- None") + "\n"
        
        return context
