import asyncio
import json
from fastapi import WebSocket
from app.services.llm import llm_service
from app.rag.retriever import rag_retriever
from app.services.stt import stt_service
from app.services.tts import tts_service
from app.services.context_builder import context_builder
from app.database.connection import AsyncSessionLocal
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.meeting_repo import MeetingRepository
from app.meeting.engine import MeetingEngine
from app.tools.tools import TOOL_DEFINITIONS
import base64
import re
import time
from app.database.connection import PERFORMANCE_PROFILING, sql_metrics


class ConversationManager:
    def __init__(self, websocket: WebSocket, lead_id: int | None):
        self.websocket = websocket
        self.lead_id = lead_id
        self.state = "idle" 
        self.chat_history = []
        self.is_interrupted = False
        self.current_task = None
        self.conversation_id = None
        self.returning_context = ""
        self.system_prompt = (
            "You are an experienced, premium business consultant for PP5 Media Solutions. You are on a live voice call with a potential client.\n"
            "YOUR CORE OBJECTIVES:\n"
            "1. Build rapport and understand the user's business goals and pain points.\n"
            "2. Discuss how PP5 Media Solutions can help them, using the provided knowledge base context.\n"
            "3. Suggest scheduling a meeting with our team once you understand their needs.\n"
            "CONVERSATION STYLE & TONE:\n"
            "- Be warm, confident, curious, and professional. \n"
            "- Speak exactly like a human consultant (use contractions like \"we're\", \"it's\").\n"
            "- Keep responses concise (1-3 short sentences). Use commas for natural breathing pauses.\n"
            "- NEVER sound like a checklist or a web form. Do not ask procedural questions back-to-back.\n"
            "LEAD COLLECTION STRATEGY:\n"
            "- Do NOT immediately ask for name, email, phone, or company.\n"
            "- Gather information naturally during the conversation. \n"
            "- ONLY ask for contact info when it logically fits (e.g., asking for an email to send a proposal, or asking for a name so you know who you are speaking with).\n"
            "- If the user has already provided a piece of information, NEVER ask for it again. Use it naturally in conversation.\n"
            "TOOL EXECUTION (SILENT BACKGROUND ACTIONS):\n"
            "- You have access to tools (extract_lead_info, get_available_meeting_times, book_meeting).\n"
            "- Execute tools SILENTLY. NEVER mention to the user that you are using a tool, updating a database, saving their info, or checking a system. \n"
            "- Example: If the user says \"My name is Mohammed\", call extract_lead_info and reply smoothly: \"Nice to meet you, Mohammed. What kind of project are you looking to build?\"\n"
            "- NEVER say \"I have updated your name\" or \"I've saved your email\".\n"
            "IDENTITY & CONSTRAINTS:\n"
            "- You are an unnamed AI voice consultant. Do not adopt a human name.\n"
            "- Do not output any markdown formatting, XML, JSON, or code in your speech.\n"
            "- Protect proprietary company secrets.\n"
        )

    async def initialize_persistence(self):
        """Create a conversation record and load returning-user context."""
        try:
            # Build returning-user context via ContextBuilder
            self.returning_context = await context_builder.build(self.lead_id)

            if self.lead_id:
                async with AsyncSessionLocal() as session:
                    repo = ConversationRepository(session)
                    self.conversation_id = await repo.create_conversation(
                        lead_id=self.lead_id,
                        model_used=llm_service.model,
                        stt_model="whisper-large-v3-turbo",
                        tts_model="elevenlabs",
                    )
                print(f">>> Conversation created: {self.conversation_id} (lead={self.lead_id})")
            else:
                print(">>> No lead_id provided. Running without persistence.")
        except Exception as e:
            print(f">>> DB persistence error (init): {e}. Continuing without persistence.")
            self.conversation_id = None

    async def _persist_message(self, speaker: str, content: str, message_type: str = "voice"):
        """Save a message to the database (fire-and-forget, won't block conversation)."""
        if not self.conversation_id:
            return
        try:
            async with AsyncSessionLocal() as session:
                repo = ConversationRepository(session)
                await repo.add_message(self.conversation_id, speaker, content, message_type)
        except Exception as e:
            print(f">>> DB persistence error (message): {e}")

    async def finalize_conversation(self):
        """
        Called on disconnect. If at least 2 conversational turns happened,
        generate a summary and mark the conversation as completed.
        Also updates last_contacted on the lead.
        """
        if not self.conversation_id:
            return

        try:
            async with AsyncSessionLocal() as session:
                repo = ConversationRepository(session)
                # Count user and assistant messages in chat_history
                user_msgs = sum(1 for m in self.chat_history if m["role"] == "user")
                assistant_msgs = sum(1 for m in self.chat_history if m["role"] == "assistant")

                if user_msgs >= 2 and assistant_msgs >= 2:
                    # Generate AI summary
                    print(">>> Generating conversation summary...")
                    transcript = "\n".join(
                        f"{m['role'].upper()}: {m['content']}" for m in self.chat_history
                    )
                    summary_prompt = (
                        "You are a business analyst. Summarize the following voice conversation "
                        "between a potential client and PP5 Media Solutions' AI consultant. "
                        "Focus on: what the client wanted, key information collected, "
                        "and any next steps agreed upon. Keep it under 4 sentences. "
                        "No markdown formatting.\n\n"
                        f"TRANSCRIPT:\n{transcript}"
                    )
                    summary = await llm_service.generate_response(
                        summary_prompt, []
                    )
                    await repo.save_summary(
                        self.conversation_id,
                        summary,
                        model_name=llm_service.model,
                    )
                    print(f">>> Summary saved: {summary[:80]}...")

                await repo.end_conversation(self.conversation_id, ended_reason="disconnect")
                print(f">>> Conversation {self.conversation_id} finalized.")

            # Update last_contacted on the lead
            if self.lead_id:
                async with AsyncSessionLocal() as session:
                    repo = ConversationRepository(session)
                    await repo.update_last_contacted(self.lead_id)
        except Exception as e:
            print(f">>> DB persistence error (finalize): {e}")

    def _reset_metrics(self):
        self.metrics = {
            "stt_latency": 0.0,
            "rag_latency": 0.0,
            "llm_ttft": 0.0,
            "llm_total": 0.0,
            "tools_latency": 0.0,
            "tts_latency": 0.0,
            "start_time": time.perf_counter()
        }
        if PERFORMANCE_PROFILING:
            sql_metrics.set({"queries": 0, "transactions": 0, "time": 0.0})

    def interrupt(self):
        """Signal the current generation to stop immediately."""
        print(">>> INTERRUPT signal received. Aborting current generation.")
        self.is_interrupted = True
            
    async def process_audio_input(self, audio_data: bytes):
        """Transcribe audio, get LLM response, synthesize audio, send back."""
        self._reset_metrics()
        print("Transcribing audio...")
        t0 = time.perf_counter()
        text = await stt_service.transcribe(audio_data)
        self.metrics["stt_latency"] = time.perf_counter() - t0
        if not text:
            print("No speech detected.")
            await self.websocket.send_json({"type": "no_speech"})
            return
            
        print(f"Transcribed: {text}")
        await self.websocket.send_json({"type": "transcript", "text": text})
        await self._process_text_and_respond(text, return_audio=True)

    async def process_user_input(self, text: str):
        """Processes the user input (text only) through the RAG and LLM."""
        self._reset_metrics()
        await self._process_text_and_respond(text, return_audio=False)

    async def _handle_tool_calls(self, tool_calls):
        """Execute tool calls from the LLM and return the results as messages."""
        results = []
        for tc in tool_calls:
            # Handle both object-based (non-stream) and dict-based (stream) tool calls
            is_dict = isinstance(tc, dict)
            func_name = tc["function"]["name"] if is_dict else tc.function.name
            tc_id = tc["id"] if is_dict else tc.id
            arguments_str = tc["function"]["arguments"] if is_dict else tc.function.arguments

            try:
                args = json.loads(arguments_str) if arguments_str else {}
            except json.JSONDecodeError:
                args = {}

            print(f">>> Tool call: {func_name}({args})")

            if func_name == "get_available_meeting_times":
                async with AsyncSessionLocal() as session:
                    meeting_repo = MeetingRepository(session)
                    engine = MeetingEngine(meeting_repo)
                    slots = await engine.get_available_times()
                result_content = json.dumps(slots)

            elif func_name == "book_meeting":
                if self.lead_id:
                    async with AsyncSessionLocal() as session:
                        meeting_repo = MeetingRepository(session)
                        engine = MeetingEngine(meeting_repo)
                        meeting = await engine.book(
                            date_str=args["date"],
                            time_str=args["time"],
                            lead_id=self.lead_id,
                        )
                    if meeting:
                        # Look up lead email for the notification
                        lead_email = "Unknown"
                        if self.lead_id:
                            async with AsyncSessionLocal() as session:
                                repo = ConversationRepository(session)
                                lead = await repo.get_lead(self.lead_id)
                                if lead:
                                    lead_email = lead.email

                        from app.email.sender import send_meeting_email
                        asyncio.create_task(send_meeting_email(
                            args["date"], args["time"], lead_email, "Booked via AI Voice Agent"
                        ))
                        result_content = json.dumps({
                            "success": True,
                            "message": f"Meeting booked for {args['date']} at {args['time']}",
                        })
                    else:
                        result_content = json.dumps({
                            "success": False,
                            "message": "That slot is no longer available. Please try another time.",
                        })
                else:
                    result_content = json.dumps({
                        "success": False,
                        "message": "Cannot book meeting – no active lead.",
                    })
            elif func_name == "extract_lead_info":
                if self.lead_id:
                    # RATIONALE: We intentionally keep this database write synchronous.
                    # While making it asynchronous via asyncio.create_task() would reduce latency, 
                    # a synchronous write ensures strict data consistency, preventing 
                    # silent failures where the AI thinks the data was saved but the DB transaction fails.
                    # Future Enhancement: We could implement a durable transactional outbox or Redis queue
                    # to achieve low-latency without sacrificing consistency guarantees.
                    async with AsyncSessionLocal() as session:
                        repo = ConversationRepository(session)
                        await repo.update_lead(self.lead_id, args)
                    result_content = json.dumps({"success": True, "message": "Lead info updated successfully."})
                else:
                    result_content = json.dumps({"success": False, "message": "Cannot update lead - no active lead."})
            else:
                result_content = json.dumps({"error": f"Unknown tool: {func_name}"})

            results.append({
                "role": "tool",
                "tool_call_id": tc_id,
                "content": result_content,
            })

        return results

    async def _process_text_and_respond(self, text: str, return_audio: bool):
        print(f"User says: {text}")
        self.is_interrupted = False
        
        try:
            if return_audio:
                await self.websocket.send_json({"type": "response_start"})

            self.chat_history.append({"role": "user", "content": text})
            # Persist user message
            asyncio.create_task(self._persist_message("user", text))
            
            t0 = time.perf_counter()
            context = await asyncio.to_thread(rag_retriever.retrieve, text, 3)
            self.metrics["rag_latency"] = time.perf_counter() - t0
            print("Successfully retrieved RAG context.")
            
            # Build the full prompt with returning-user context (from ContextBuilder)
            prompt = (
                f"{self.system_prompt}\n\n"
                f"{self.returning_context}\n"
                f"Here are 3 relevant context chunks from our knowledge base:\n"
                f"--- START CONTEXT ---\n{context}\n--- END CONTEXT ---\n"
            )

            # Keep the last 20 messages (10 turns) to prevent token explosion
            recent_history = self.chat_history[-20:] if len(self.chat_history) > 20 else self.chat_history
            messages = [{"role": "system", "content": prompt}] + recent_history

            async def combined_stream_gen():
                t_llm_start = time.perf_counter()
                stream = await llm_service.client.chat.completions.create(
                    model=llm_service.model,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=512,
                    stream=True,
                )
                
                tool_calls = []
                async for chunk in stream:
                    if self.metrics["llm_ttft"] == 0.0:
                        self.metrics["llm_ttft"] = time.perf_counter() - t_llm_start
                    
                    delta = chunk.choices[0].delta
                    if delta.tool_calls:
                        print(f"[{time.time():.4f}] [TRACE] Tool Call Detected in LLM stream")
                        for tc_chunk in delta.tool_calls:
                            while len(tool_calls) <= tc_chunk.index:
                                tool_calls.append({
                                    "id": tc_chunk.id, 
                                    "type": "function", 
                                    "function": {"name": tc_chunk.function.name if tc_chunk.function.name else "", "arguments": ""}
                                })
                            if tc_chunk.function.arguments:
                                tool_calls[tc_chunk.index]["function"]["arguments"] += tc_chunk.function.arguments
                    elif delta.content:
                        yield delta.content
                
                if tool_calls:
                    self.chat_history.append({
                        "role": "assistant",
                        "content": "",
                        "tool_calls": tool_calls,
                    })
                    
                    t_tool_start = time.perf_counter()
                    tool_results = await self._handle_tool_calls(tool_calls)
                    self.metrics["tools_latency"] = time.perf_counter() - t_tool_start
                    
                    for tr in tool_results:
                        self.chat_history.append(tr)
                    
                    recent_history = self.chat_history[-20:] if len(self.chat_history) > 20 else self.chat_history
                    new_messages = [{"role": "system", "content": prompt}] + recent_history
                    t_second_llm_start = time.perf_counter()
                    print(f"[{time.time():.4f}] [TRACE] Second LLM Request Begins")
                    new_stream = await llm_service.client.chat.completions.create(
                        model=llm_service.model,
                        messages=new_messages,
                        temperature=0.7,
                        max_tokens=512,
                        stream=True,
                    )
                    second_llm_ttft = 0.0
                    async for new_chunk in new_stream:
                        if second_llm_ttft == 0.0:
                            second_llm_ttft = time.perf_counter() - t_second_llm_start
                            print(f"[{time.time():.4f}] [TRACE] Second LLM Response Received. TTFT: {second_llm_ttft:.4f}s")
                        if new_chunk.choices[0].delta.content:
                            yield new_chunk.choices[0].delta.content
                
                self.metrics["llm_total"] += time.perf_counter() - t_llm_start

            print("Generating streamed LLM response...")
            await self._stream_and_send(combined_stream_gen(), return_audio)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            err_msg = f"Error in processing: {e}"
            await self.websocket.send_json({"type": "error", "message": err_msg})
            await self.websocket.send_json({"type": "response_complete", "text": "I'm sorry, I encountered an error while processing that."})
            if return_audio:
                err_audio = await asyncio.to_thread(tts_service.synthesize, "I'm sorry, I encountered an error while processing that.")
                if err_audio:
                    b64_audio = base64.b64encode(err_audio).decode('utf-8')
                    await self.websocket.send_json({"type": "audio", "data": b64_audio})

    async def _stream_and_synthesize(self, messages: list, return_audio: bool):
        """Stream LLM response from messages (after tool call), synthesize and send."""
        try:
            stream = await llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=messages,
                temperature=0.7,
                max_tokens=512,
                stream=True,
            )

            async def gen():
                async for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content

            await self._stream_and_send(gen(), return_audio)
        except Exception as e:
            print(f">>> Error in stream_and_synthesize: {e}")

    async def _stream_and_send(self, stream_gen, return_audio: bool):
        """Core streaming + TTS synthesis + WebSocket send logic."""
        full_response = ""
        current_buffer = ""
        sentences_in_buffer = 0
        
        sentence_end_pattern = re.compile(r'(?<=[.!?])\s+|(?<=[.!?])$')

        audio_queue = asyncio.Queue()

        async def audio_worker():
            while True:
                text_chunk = await audio_queue.get()
                if text_chunk is None:
                    audio_queue.task_done()
                    break
                
                if self.is_interrupted:
                    audio_queue.task_done()
                    continue
                
                try:
                    # Strip out any accidentally leaked XML tags (e.g. <function=...>)
                    text_chunk = re.sub(r'<[^>]+>', '', text_chunk).strip()
                    if not text_chunk:
                        continue

                    audio_bytes = None
                    if return_audio:
                        print(f"[{time.time():.4f}] [TRACE] TTS Starts for chunk: {text_chunk[:20]}...")
                        t_tts = time.perf_counter()
                        audio_bytes = await asyncio.to_thread(tts_service.synthesize, text_chunk)
                        self.metrics["tts_latency"] += time.perf_counter() - t_tts
                        
                    await self.websocket.send_json({"type": "response_chunk", "text": text_chunk})
                    
                    if return_audio and audio_bytes and not self.is_interrupted:
                        b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
                        await self.websocket.send_json({"type": "audio", "data": b64_audio})
                        print(f"[{time.time():.4f}] [TRACE] Frontend Receives Response (Audio Chunk)")
                except Exception as e:
                    print(f"Error in audio worker: {e}")
                finally:
                    audio_queue.task_done()

        worker_task = asyncio.create_task(audio_worker())
        sent_length = 0

        async for chunk in stream_gen:
            if self.is_interrupted:
                print(">>> Generation aborted by interrupt.")
                break
            
            full_response += chunk
            current_buffer += chunk
            
            if sentence_end_pattern.search(current_buffer):
                parts = sentence_end_pattern.split(current_buffer)
                
                for i in range(len(parts) - 1):
                    if self.is_interrupted:
                        break
                    sentence = parts[i].strip()
                    if sentence:
                        sentences_in_buffer += 1
                
                current_buffer = parts[-1]
                
                if sentences_in_buffer >= 1:
                    batch_text = full_response[:len(full_response) - len(current_buffer)].strip()
                    new_text = batch_text[sent_length:].strip()
                    if new_text:
                        await audio_queue.put(new_text)
                        sent_length = len(batch_text)
                    sentences_in_buffer = 0

        if not self.is_interrupted:
            remaining = full_response[sent_length:].strip()
            if remaining:
                await audio_queue.put(remaining)
            
        await audio_queue.put(None)
        await worker_task
        
        if not self.is_interrupted:
            await self.websocket.send_json({"type": "response_complete", "text": full_response})
        
        if full_response:
            self.chat_history.append({"role": "assistant", "content": full_response})
            # Persist assistant message
            asyncio.create_task(self._persist_message("assistant", full_response))
        print(f"Finished response. Interrupted: {self.is_interrupted}")
        
        if PERFORMANCE_PROFILING and not self.is_interrupted:
            total_time = time.perf_counter() - self.metrics["start_time"]
            db_metrics = sql_metrics.get()
            print("\n" + "="*50)
            print(" PERFORMANCE PROFILING REPORT")
            print("="*50)
            print(f" STT Latency:          {self.metrics.get('stt_latency', 0.0)*1000:.2f} ms")
            print(f" RAG Latency:          {self.metrics.get('rag_latency', 0.0)*1000:.2f} ms")
            print(f" LLM TTFT:             {self.metrics.get('llm_ttft', 0.0)*1000:.2f} ms")
            print(f" LLM Total Gen Time:   {self.metrics.get('llm_total', 0.0)*1000:.2f} ms")
            print(f" Tool Exec Time:       {self.metrics.get('tools_latency', 0.0)*1000:.2f} ms")
            print(f" SQL Query Count:      {db_metrics['queries']}")
            print(f" SQL Exec Time:        {db_metrics['time']*1000:.2f} ms")
            print(f" SQL Transactions:     {db_metrics['transactions']}")
            print(f" TTS Total Latency:    {self.metrics.get('tts_latency', 0.0)*1000:.2f} ms")
            print(f" End-to-End Latency:   {total_time*1000:.2f} ms")
            print("="*50 + "\n")
