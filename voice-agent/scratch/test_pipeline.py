import asyncio
import sys

async def run_test():
    sys.path.append(r"c:\Projects\Website Voice Agent\voice-agent")
    
    from app.services.conversation_manager import ConversationManager

    class MockWebSocket:
        def __init__(self):
            self.sent_messages = []
            
        async def send_json(self, data):
            self.sent_messages.append(data)
            if data.get("type") == "response_chunk":
                print(f"UI Chunk: {data['text']}")
            elif data.get("type") == "response_complete":
                print(f"\nFinal Response: {data['text']}")
                
    ws = MockWebSocket()
    manager = ConversationManager(ws, visitor_id="test_visitor_mohammed")
    
    print("--- Init ---")
    await manager.initialize_persistence()
    
    print("\n--- Sending Input ---")
    await manager.process_user_input("My name is Mohammed and my email is mo@test.com")
    
    print("\n--- Testing Meeting ---")
    await manager.process_user_input("I'd like to schedule a meeting on 2026-07-02 at 14:00")
    
if __name__ == "__main__":
    asyncio.run(run_test())