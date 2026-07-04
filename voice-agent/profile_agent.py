import asyncio
import time
import uuid
import json
from unittest.mock import AsyncMock, MagicMock

# Set up logging for our profiler
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

class MockWebSocket:
    def __init__(self):
        self.sent_messages = []
    
    async def accept(self):
        pass
    
    async def send_json(self, data):
        self.sent_messages.append(data)
        
    async def receive(self):
        return {"text": "dummy"}
        
    async def close(self):
        pass

async def profile():
    from app.services.conversation_manager import ConversationManager
    from app.rag.retriever import rag_retriever
    from app.services.llm import llm_service
    from app.services.tts import tts_service
    from app.meeting.engine import MeetingEngine
    from app.repositories.conversation_repo import ConversationRepository

    print("--- PROFILING INITIALIZATION ---")
    ws = MockWebSocket()
    manager = ConversationManager(ws, visitor_id="test_visitor_123")
    
    t0 = time.perf_counter()
    await manager.initialize_persistence()
    t1 = time.perf_counter()
    print(f"initialize_persistence: {(t1-t0)*1000:.2f} ms")

    print("\n--- PROFILING NORMAL CONVERSATION (No Tools) ---")
    
    # Patch RAG
    original_retrieve = rag_retriever.retrieve
    def mocked_retrieve(query, top_k):
        rt0 = time.perf_counter()
        res = original_retrieve(query, top_k)
        rt1 = time.perf_counter()
        print(f"RAG retrieval: {(rt1-rt0)*1000:.2f} ms")
        return res
    rag_retriever.retrieve = mocked_retrieve

    # Patch TTS
    original_synthesize = tts_service.synthesize
    def mocked_synthesize(text):
        tt0 = time.perf_counter()
        # res = original_synthesize(text)
        # We mock TTS completely to not slow down our python script unnecessarily, 
        # or we can let it run once to see real TTS latency. Let's let it run but measure it.
        res = b'dummy_audio' # Skipping real TTS because Kokoro takes ~10s on CPU
        tt1 = time.perf_counter()
        print(f"TTS generation (Mocked): {(tt1-tt0)*1000:.2f} ms")
        return res
    tts_service.synthesize = mocked_synthesize

    t0 = time.perf_counter()
    await manager.process_user_input("What are your services?")
    
    # Wait for the audio_worker task to finish
    await asyncio.sleep(2)
    t1 = time.perf_counter()
    
    print("\n--- PROFILING LEAD CAPTURE TOOL ---")
    t0 = time.perf_counter()
    # Mock LLM to force tool call for lead capture
    async def mock_handle_tool_calls(tool_calls):
        ht0 = time.perf_counter()
        results = []
        for tc in tool_calls:
            print(f"Executing tool: {tc['function']['name']}")
            if tc['function']['name'] == 'update_lead_info':
                # Call the real implementation to measure DB time
                # We need to construct a mock tool call object that matches the expected structure
                class MockTool:
                    id = "call_123"
                    class Func:
                        name = "update_lead_info"
                        arguments = '{"name": "John Doe", "email": "john@example.com"}'
                    function = Func()
                
                trt0 = time.perf_counter()
                res = await manager._handle_tool_calls([MockTool()])
                trt1 = time.perf_counter()
                print(f"Tool execution (update_lead_info): {(trt1-trt0)*1000:.2f} ms")
                results.extend(res)
        ht1 = time.perf_counter()
        return results
        
    await mock_handle_tool_calls([{"function": {"name": "update_lead_info"}}])

    print("\n--- PROFILING GET AVAILABLE MEETING TIMES TOOL ---")
    async def measure_get_times():
        class MockTool:
            id = "call_456"
            class Func:
                name = "get_available_meeting_times"
                arguments = '{}'
            function = Func()
        
        trt0 = time.perf_counter()
        res = await manager._handle_tool_calls([MockTool()])
        trt1 = time.perf_counter()
        print(f"Tool execution (get_available_meeting_times): {(trt1-trt0)*1000:.2f} ms")
        
    await measure_get_times()

    print("\n--- PROFILING BOOK MEETING TOOL ---")
    async def measure_book_meeting():
        class MockTool:
            id = "call_789"
            class Func:
                name = "book_meeting"
                arguments = '{"date": "2026-07-02", "time": "14:00"}'
            function = Func()
        
        trt0 = time.perf_counter()
        res = await manager._handle_tool_calls([MockTool()])
        trt1 = time.perf_counter()
        print(f"Tool execution (book_meeting): {(trt1-trt0)*1000:.2f} ms")
        
    await measure_book_meeting()

if __name__ == "__main__":
    asyncio.run(profile())
