import asyncio
from app.services.lead_state import LeadStateManager

async def test_state_manager():
    # Mocking for sandbox DB without spinning up the real DB
    manager = LeadStateManager(lead_id=None)
    
    print("Initial Context:")
    print(manager.get_prompt_context())
    
    print("\nSimulating LLM extraction...")
    manager.update_extracted_info({
        "name": "Alex",
        "budget": None,
        "budget_reason": "Alex declined to share their budget."
    })
    
    print("\nUpdated Context:")
    print(manager.get_prompt_context())
    
    print("\nUncommitted Changes Count:", manager.uncommitted_changes)
    
if __name__ == "__main__":
    asyncio.run(test_state_manager())
