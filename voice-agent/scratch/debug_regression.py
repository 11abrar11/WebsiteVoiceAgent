import asyncio
import time
from app.services.lead_state import LeadStateManager
from app.services.conversation_manager import ConversationManager
from app.database.connection import AsyncSessionLocal
from app.repositories.conversation_repo import ConversationRepository

class MockWebsocket:
    async def send_json(self, data):
        if "text" in data:
            print(f"WS SEND: {data['text']}")
        elif "type" in data:
            print(f"WS SEND TYPE: {data['type']}")

async def main():
    print("--- Setting up DB lead ---")
    async with AsyncSessionLocal() as session:
        repo = ConversationRepository(session)
        # Check if test lead exists
        lead = await repo.get_lead_by_email("regression_test@example.com")
        if not lead:
            lead = await repo.create_lead("regression_test@example.com")
        lead_id = lead.id
        await session.commit()
        
    print(f"--- Lead ID: {lead_id} ---")

    cm = ConversationManager(websocket=MockWebsocket(), lead_id=lead_id)
    await cm.initialize_persistence()

    # Simulate STT -> Process
    print("\n\n--- 1. Testing info extraction ---")
    await cm.process_user_input("My name is Test User and my company is Test Inc.")
    
    print("\n\n--- 2. Waiting for inactivity commit ---")
    # Actually _inactivity_committer is running, but let's test book_meeting
    
    print("\n\n--- 3. Testing book meeting ---")
    await cm.process_user_input("I want to book a meeting for 2026-07-06 at 10:00.")

    await asyncio.sleep(2)
    print("\n\n--- 4. Disconnecting (Finalize) ---")
    await cm.finalize_conversation()

if __name__ == "__main__":
    asyncio.run(main())
