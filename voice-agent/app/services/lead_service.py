from app.database.connection import AsyncSessionLocal
from app.repositories.conversation_repo import ConversationRepository
from app.models.lead import Lead

class LeadService:
    async def get_or_create_lead(self, email: str):
        async with AsyncSessionLocal() as session:
            repo = ConversationRepository(session)
            lead = await repo.get_lead_by_email(email)
            is_new = False
            if not lead:
                lead = await repo.create_lead(email)
                is_new = True
            return lead, is_new

lead_service = LeadService()