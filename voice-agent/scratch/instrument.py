import sys

# 1. Instrument LeadStateManager
with open("app/services/lead_state.py", "r") as f:
    state_content = f.read()

state_content = state_content.replace(
    "self.uncommitted_changes = 0\n        self.last_update_time = time.time()\n        self._lock = asyncio.Lock()",
    "self.uncommitted_changes = 0\n        self.last_update_time = time.time()\n        self._lock = asyncio.Lock()\n        print(f'[TRACE] LeadStateManager initialized for lead {self.lead_id}')"
)

state_content = state_content.replace(
    'self.last_update_time = time.time()',
    'self.last_update_time = time.time()\n        print(f"[TRACE] LeadStateManager.update() - Dirty fields: {self.uncommitted_changes}")\n        print(f"[TRACE] Current Lead State: {self.get_prompt_context()}")',
    1 # only first occurrence (in update_extracted_info)
)

commit_start = """    async def commit(self):
        \"\"\"Perform a single batched database update.\"\"\"
        if not self.lead_id or self.uncommitted_changes == 0:
            return"""
commit_log = """    async def commit(self):
        \"\"\"Perform a single batched database update.\"\"\"
        print(f"[TRACE] Commit decision: uncommitted_changes={self.uncommitted_changes}, lead_id={self.lead_id}")
        if not self.lead_id or self.uncommitted_changes == 0:
            return"""
state_content = state_content.replace(commit_start, commit_log)

commit_sql = """                try:
                    async with AsyncSessionLocal() as session:
                        repo = ConversationRepository(session)
                        await repo.update_lead(self.lead_id, update_payload)
                    print(f">>> LeadStateManager committed {self.uncommitted_changes} changes for lead {self.lead_id}")"""
commit_sql_log = """                try:
                    print("[TRACE] LeadStateManager.commit() executing payload")
                    async with AsyncSessionLocal() as session:
                        repo = ConversationRepository(session)
                        await repo.update_lead(self.lead_id, update_payload)
                    print(f"[TRACE] LeadState reset. >>> LeadStateManager committed {self.uncommitted_changes} changes for lead {self.lead_id}")"""
state_content = state_content.replace(commit_sql, commit_sql_log)

with open("app/services/lead_state.py", "w") as f:
    f.write(state_content)

# 2. Instrument ConversationManager
with open("app/services/conversation_manager.py", "r") as f:
    cm_content = f.read()

cm_content = cm_content.replace(
    'print(f"User says: {text}")',
    'print(f"[TRACE] User message received: {text}")'
)

cm_content = cm_content.replace(
    'print(f">>> Tool call: {func_name}({args})")',
    'print(f"[TRACE] LLM response (Tool Call): {func_name}({args})")'
)

cm_content = cm_content.replace(
    'async def process_user_input(self, text: str):',
    'async def process_user_input(self, text: str):\n        print("[TRACE] Conversation starts")'
)

with open("app/services/conversation_manager.py", "w") as f:
    f.write(cm_content)

# 3. Instrument ConversationRepo update_lead
with open("app/repositories/conversation_repo.py", "r") as f:
    repo_content = f.read()

repo_start = """    async def update_lead(self, lead_id: int, data: dict) -> Lead | None:
        \"\"\"Update lead fields and recalculate data_completeness.\"\"\"
        lead = await self.get_lead(lead_id)
        if not lead:
            return None"""
repo_log = """    async def update_lead(self, lead_id: int, data: dict) -> Lead | None:
        \"\"\"Update lead fields and recalculate data_completeness.\"\"\"
        print(f"[TRACE] Repository.update_lead() called with data: {data}")
        lead = await self.get_lead(lead_id)
        if not lead:
            return None"""
repo_content = repo_content.replace(repo_start, repo_log)

repo_commit = """        await self.session.commit()
        await self.session.refresh(lead)"""
repo_commit_log = """        print(f"[TRACE] SQL execution (Session state dirty: {self.session.dirty})")
        await self.session.commit()
        print("[TRACE] Transaction commit successful")
        await self.session.refresh(lead)"""
repo_content = repo_content.replace(repo_commit, repo_commit_log)

with open("app/repositories/conversation_repo.py", "w") as f:
    f.write(repo_content)

print("Instrumentation injected.")
