import sys

def add_trace(filepath, replacements):
    with open(filepath, "r") as f:
        content = f.read()
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
        else:
            print(f"Warning: Could not find '{old}' in {filepath}")
            
    with open(filepath, "w") as f:
        f.write(content)

cm_replacements = [
    # 1. User Message (in process_user_input)
    ('async def process_user_input(self, text: str):',
     'async def process_user_input(self, text: str):\n        import time\n        print(f"[{time.time():.4f}] [TRACE] User Message Received: {text}")'),
    
    # 2. LLM Response / Tool Call Detected (in combined_stream_gen)
    ('if chunk.choices[0].delta.tool_calls:',
     'if chunk.choices[0].delta.tool_calls:\n                print(f"[{time.time():.4f}] [TRACE] Tool Call Detected in LLM stream")'),
    
    # 3. Tool Arguments Parsed (in combined_stream_gen)
    ('tool_results = await self._handle_tool_calls(tool_calls)',
     'print(f"[{time.time():.4f}] [TRACE] Tool Arguments Parsed: {tool_calls}")\n                    t_before_handle = time.perf_counter()\n                    print(f"[{time.time():.4f}] [TRACE] ENTER ConversationManager._handle_tool_calls()")\n                    tool_results = await self._handle_tool_calls(tool_calls)\n                    print(f"[{time.time():.4f}] [TRACE] EXIT ConversationManager._handle_tool_calls() - Duration: {time.perf_counter() - t_before_handle:.4f}s")\n                    print(f"[{time.time():.4f}] [TRACE] Tool Result Returned: {tool_results}")'),

    # 4. Second LLM Request Begins (in combined_stream_gen)
    ('stream2 = await llm_service.client.chat.completions.create(',
     'print(f"[{time.time():.4f}] [TRACE] Second LLM Request Begins")\n            stream2 = await llm_service.client.chat.completions.create('),
    
    # 5. Second LLM Response Received (in combined_stream_gen)
    ('async for chunk in stream2:',
     'print(f"[{time.time():.4f}] [TRACE] Second LLM Response Stream Started")\n            async for chunk in stream2:'),

    # 6. TTS Starts (in _stream_and_send)
    ('audio_stream = await self.tts.generate_audio_stream(text)',
     'import time\n            print(f"[{time.time():.4f}] [TRACE] TTS Starts for text: {text[:20]}...")\n            audio_stream = await self.tts.generate_audio_stream(text)'),
    
    # 7. Frontend Receives Response (in _stream_and_send)
    ('await self.websocket.send_json({"type": "audio", "audio": audio_b64})',
     'await self.websocket.send_json({"type": "audio", "audio": audio_b64})\n                        print(f"[{time.time():.4f}] [TRACE] Frontend Receives Response (Audio Chunk)")'),
]

ls_replacements = [
    # 1. ENTER / EXIT LeadStateManager.update()
    ('def update_extracted_info(self, extracted_data: Dict[str, Any]):',
     'def update_extracted_info(self, extracted_data: Dict[str, Any]):\n        import time\n        print(f"[{time.time():.4f}] [TRACE] ENTER LeadStateManager.update() with data: {extracted_data}")'),
    
    ('self.last_update_time = time.time()',
     'self.last_update_time = time.time()\n        print(f"[{time.time():.4f}] [TRACE] Dirty fields: {self.uncommitted_changes}")\n        print(f"[{time.time():.4f}] [TRACE] EXIT LeadStateManager.update()")\n        print(f"[{time.time():.4f}] [TRACE] Commit required? {\'YES\' if self.uncommitted_changes > 0 else \'NO\'}")'),

    # 2. ENTER / EXIT LeadStateManager.commit()
    ('async def commit(self):',
     'async def commit(self):\n        import time\n        print(f"[{time.time():.4f}] [TRACE] ENTER LeadStateManager.commit() - uncommitted_changes={self.uncommitted_changes}")'),
    
    ('print(f">>> DB commit failed: {e}")',
     'print(f"[{time.time():.4f}] [TRACE] Commit failed with exception: {e}")'),
    
    ('self.uncommitted_changes = 0\n            self.last_update_time = time.time()',
     'self.uncommitted_changes = 0\n            self.last_update_time = time.time()\n            print(f"[{time.time():.4f}] [TRACE] EXIT LeadStateManager.commit()")')
]

# We need to target the return block if commit skipped
ls_replacements.append((
    'if not self.lead_id or self.uncommitted_changes == 0:\n            return',
    'if not self.lead_id or self.uncommitted_changes == 0:\n            print(f"[{time.time():.4f}] [TRACE] EXIT LeadStateManager.commit() - Skipped because lead_id={self.lead_id}, uncommitted_changes={self.uncommitted_changes}")\n            return'
))

repo_replacements = [
    # ConversationRepo update_lead
    ('async def update_lead(self, lead_id: int, data: dict) -> Lead | None:',
     'async def update_lead(self, lead_id: int, data: dict) -> Lead | None:\n        import time\n        print(f"[{time.time():.4f}] [TRACE] Repository Method: ConversationRepository.update_lead()")'),
    
    ('await self.session.commit()',
     'import time\n        print(f"[{time.time():.4f}] [TRACE] SQL Execution starting")\n        await self.session.commit()\n        print(f"[{time.time():.4f}] [TRACE] Transaction Commit Successful")'),
]

engine_replacements = [
    # Meeting Engine
    ('async def book(self, date_str: str, time_str: str, lead_id: int, notes: str = None):',
     'async def book(self, date_str: str, time_str: str, lead_id: int, notes: str = None):\n        import time\n        print(f"[{time.time():.4f}] [TRACE] MeetingEngine.book() ENTER")'),
]

add_trace("app/services/conversation_manager.py", cm_replacements)
add_trace("app/services/lead_state.py", ls_replacements)
add_trace("app/repositories/conversation_repo.py", repo_replacements)
add_trace("app/meeting/engine.py", engine_replacements)
print("Instrumentation complete.")
