"""
Repository for lead, conversation, message, and summary CRUD operations.
All methods use integer lead_id / conversation_id — no email logic here.
"""
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message
from app.models.conversation_summary import ConversationSummary


class ConversationRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Lead operations ──────────────────────────────────────────────

    async def get_lead_by_email(self, email: str) -> Lead | None:
        """Find a lead by their normalised email address."""
        result = await self.session.execute(
            select(Lead).where(Lead.email == email)
        )
        return result.scalar_one_or_none()

    async def create_lead(self, email: str) -> Lead:
        """Create a new lead record with the given email."""
        lead = Lead(email=email)
        self.session.add(lead)
        await self.session.commit()
        await self.session.refresh(lead)
        return lead

    async def get_lead(self, lead_id: int) -> Lead | None:
        """Fetch a lead by integer PK."""
        result = await self.session.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        return result.scalar_one_or_none()

    async def get_lead_profile(self, lead_id: int) -> dict | None:
        """Return a structured lead profile dict for LLM context injection."""
        lead = await self.get_lead(lead_id)
        if not lead:
            return None

        profile_fields = [
            "name", "phone", "company", "industry", "requirement",
            "monthly_leads", "company_size", "budget", "timeline",
            "decision_maker", "lead_status",
        ]
        profile = {}
        filled = 0
        for field in profile_fields:
            value = getattr(lead, field, None)
            profile[field] = value
            if value:
                filled += 1
        profile["email"] = lead.email
        profile["data_completeness"] = round(filled / len(profile_fields), 2) if profile_fields else 0.0
        profile["missing_fields"] = [f for f in profile_fields if not getattr(lead, f, None)]
        return profile

    async def update_lead(self, lead_id: int, data: dict) -> Lead | None:
        """Update lead fields and recalculate data_completeness."""
        lead = await self.get_lead(lead_id)
        if not lead:
            return None

        for k, v in data.items():
            if hasattr(lead, k) and v is not None:
                setattr(lead, k, v)

        # Recalculate data completeness
        profile_fields = [
            "name", "phone", "company", "industry", "requirement",
            "monthly_leads", "company_size", "budget", "timeline",
            "decision_maker",
        ]
        filled = sum(1 for f in profile_fields if getattr(lead, f, None))
        lead.data_completeness = round(filled / len(profile_fields), 2)

        await self.session.commit()
        await self.session.refresh(lead)
        return lead

    async def update_last_contacted(self, lead_id: int):
        """Set the lead's last_contacted timestamp to now."""
        lead = await self.get_lead(lead_id)
        if lead:
            lead.last_contacted = datetime.now(timezone.utc)
            await self.session.commit()

    # ── Conversation operations ──────────────────────────────────────

    async def create_conversation(self, lead_id: int, model_used: str = None,
                                   stt_model: str = None, tts_model: str = None) -> int:
        """Create a new conversation record and return its integer ID."""
        conversation = Conversation(
            lead_id=lead_id,
            model_used=model_used,
            stt_model=stt_model,
            tts_model=tts_model,
        )
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation.id

    async def end_conversation(self, conversation_id: int,
                                status: ConversationStatus = ConversationStatus.COMPLETED,
                                ended_reason: str = "disconnect"):
        """Mark a conversation as ended and populate duration metadata."""
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            now = datetime.now(timezone.utc)
            conversation.ended_at = now
            conversation.status = status
            conversation.ended_reason = ended_reason

            # Calculate duration
            if conversation.started_at:
                delta = now - conversation.started_at
                conversation.duration_seconds = round(delta.total_seconds(), 1)

            # Count messages
            msg_count = await self.session.execute(
                select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
            )
            conversation.message_count = msg_count.scalar() or 0

            await self.session.commit()

    async def add_message(self, conversation_id: int, speaker: str,
                          content: str, message_type: str = "voice"):
        """Add a message to the transcript."""
        message = Message(
            conversation_id=conversation_id,
            speaker=speaker,
            content=content,
            message_type=message_type,
        )
        self.session.add(message)
        await self.session.commit()

    async def save_summary(self, conversation_id: int, summary_text: str,
                           model_name: str = None):
        """Save an AI-generated conversation summary with versioning metadata."""
        summary = ConversationSummary(
            conversation_id=conversation_id,
            summary=summary_text,
            summary_version=1,
            summary_model=model_name,
        )
        self.session.add(summary)
        await self.session.commit()

    async def get_recent_summaries(self, lead_id: int, limit: int = 3) -> list[str]:
        """Fetch the last N conversation summaries for a lead."""
        result = await self.session.execute(
            select(ConversationSummary)
            .join(Conversation, ConversationSummary.conversation_id == Conversation.id)
            .where(Conversation.lead_id == lead_id)
            .order_by(ConversationSummary.generated_at.desc())
            .limit(limit)
        )
        summaries = result.scalars().all()
        return [s.summary for s in reversed(summaries)]  # chronological order

    # ── Dashboard queries ────────────────────────────────────────────

    async def get_conversation(self, conversation_id: int):
        """Get a conversation with all its relationships eagerly loaded."""
        result = await self.session.execute(
            select(Conversation)
            .options(
                selectinload(Conversation.messages),
                selectinload(Conversation.lead),
                selectinload(Conversation.summary),
            )
            .where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_all_conversations(self, limit: int = 50, offset: int = 0):
        """Get a paginated list of conversations with lead info."""
        result = await self.session.execute(
            select(Conversation)
            .options(
                selectinload(Conversation.lead),
                selectinload(Conversation.summary),
            )
            .order_by(Conversation.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def count_conversations(self) -> int:
        """Return total number of conversations."""
        result = await self.session.execute(
            select(func.count(Conversation.id))
        )
        return result.scalar()
