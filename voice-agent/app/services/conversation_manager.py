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
from app.policy.engine import PolicyEngine
from app.policy.stage_engine import ConversationStage
from app.services.lead_state import LeadStateManager
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

        # ── Policy Engine (source of truth for all business decisions) ──
        self.policy_engine = PolicyEngine()
        self.current_stage = ConversationStage.GREETING
        self.turn_count = 0
        self.turns_since_last_extraction = 0
        self.rag_invoked_this_turn = False

        # ── LeadStateManager ──
        self.lead_state = LeadStateManager(lead_id)

    async def initialize_persistence(self):
        """Create a conversation record and load returning-user context."""
        try:
            # Build returning-user context via ContextBuilder
            self.returning_context = await context_builder.build(self.lead_id)

            # Load lead state from database
            await self.lead_state.load_from_db()

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
            # Commit any pending lead state changes
            await self.lead_state.commit()

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

    async def _handle_tool_calls(self, tool_calls, policy_decision):
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

            # ── Enterprise Policy: Validate tool call ─────────────────
            is_allowed, reason = self.policy_engine.validate_tool_call(
                func_name, args, policy_decision.allowed_tool_names,
            )
            if not is_allowed:
                print(f">>> BLOCKED tool call: {func_name} -- {reason}")
                results.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": json.dumps({"error": reason}),
                })
                continue

            print(f">>> Tool call: {func_name}({args})")

            if func_name == "get_available_meeting_times":
                async with AsyncSessionLocal() as session:
                    meeting_repo = MeetingRepository(session)
                    engine = MeetingEngine(meeting_repo)
                    slots = await engine.get_available_times()

                # Format as concise human-readable text (token optimization)
                if slots:
                    slot_lines = []
                    current_date = None
                    for s in slots:
                        if s["date"] != current_date:
                            current_date = s["date"]
                            slot_lines.append(f"\n{s['day']} {s['date']}:")
                        slot_lines.append(f"  {s['time']}")
                    result_content = "Available meeting times:" + "".join(slot_lines)
                else:
                    result_content = "No available meeting times found."

            elif func_name == "confirm_meeting_slot":
                # ── Unified meeting intent: backend decides book vs reschedule ──
                if self.lead_id:
                    meeting_pol = policy_decision.meeting_policy

                    if meeting_pol.should_reschedule and meeting_pol.active_meeting_id:
                        # Reschedule flow: cancel old + book new
                        async with AsyncSessionLocal() as session:
                            meeting_repo = MeetingRepository(session)
                            engine = MeetingEngine(meeting_repo)
                            meeting = await engine.reschedule(
                                old_meeting_id=meeting_pol.active_meeting_id,
                                new_date_str=args["date"],
                                new_time_str=args["time"],
                                lead_id=self.lead_id,
                            )
                        if meeting:
                            result_content = json.dumps({
                                "success": True,
                                "message": f"Meeting rescheduled to {args['date']} at {args['time']}",
                                "action": "rescheduled",
                            })
                        else:
                            result_content = json.dumps({
                                "success": False,
                                "message": "That slot is no longer available. Please try another time.",
                            })
                    else:
                        # New booking flow
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
                                "action": "booked",
                            })
                        else:
                            result_content = json.dumps({
                                "success": False,
                                "message": "That slot is no longer available. Please try another time.",
                            })
                else:
                    result_content = json.dumps({
                        "success": False,
                        "message": "Cannot manage meeting - no active lead.",
                    })

            elif func_name == "extract_lead_info":
                if self.lead_id:
                    # Update in-memory lead state
                    self.lead_state.update_extracted_info(args)
                    self.turns_since_last_extraction = 0

                    # Commit to database
                    await self.lead_state.commit()

                    result_content = json.dumps({"success": True, "message": "Lead info updated."})
                else:
                    result_content = json.dumps({"success": False, "message": "No active lead."})

            elif func_name == "search_knowledge_base":
                # ── Dynamic RAG: only invoked when the tool is called ──
                query = args.get("query", "")
                t_rag = time.perf_counter()
                context = await asyncio.to_thread(rag_retriever.retrieve, query, 2)
                self.metrics["rag_latency"] = time.perf_counter() - t_rag
                self.rag_invoked_this_turn = True

                if PERFORMANCE_PROFILING:
                    self.policy_engine.token_profiler.set_num_retrieved_docs(2)

                result_content = context  # Plain text, not JSON

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
        self.rag_invoked_this_turn = False
        self.turn_count += 1
        self.turns_since_last_extraction += 1
        
        try:
            if return_audio:
                await self.websocket.send_json({"type": "response_start"})

            self.chat_history.append({"role": "user", "content": text})
            # Persist user message
            asyncio.create_task(self._persist_message("user", text))
            
            # ── POLICY ENGINE: Evaluate all policies before LLM request ──
            policy_decision = await self.policy_engine.evaluate(
                user_message=text,
                chat_history=self.chat_history,
                lead_state=self.lead_state,
                lead_id=self.lead_id,
                current_stage=self.current_stage,
                turn_count=self.turn_count,
                returning_context=self.returning_context,
                conversation_summary="",  # Summaries are in returning_context
                turns_since_last_extraction=self.turns_since_last_extraction,
                debug=PERFORMANCE_PROFILING,
            )

            # Update conversation stage
            self.current_stage = policy_decision.stage

            # Log the decision in debug mode
            if PERFORMANCE_PROFILING and policy_decision.decision_log:
                print(self.policy_engine.decision_logger.format_log(
                    policy_decision.decision_log
                ))

            # Build messages with the dynamic prompt (no RAG injected here)
            recent_history = self.chat_history[-10:] if len(self.chat_history) > 10 else self.chat_history
            messages = [{"role": "system", "content": policy_decision.system_prompt}] + recent_history

            # Get the gated tools for this stage
            allowed_tools = policy_decision.allowed_tools

            async def combined_stream_gen():
                t_llm_start = time.perf_counter()
                stream = await llm_service.client.chat.completions.create(
                    model=llm_service.model,
                    messages=messages,
                    tools=allowed_tools if allowed_tools else None,
                    tool_choice="auto" if allowed_tools else None,
                    temperature=0.7,
                    max_tokens=512,
                    stream=True,
                )
                
                tool_calls = []
                first_token_received = False
                async for chunk in stream:
                    if not first_token_received:
                        self.metrics["llm_ttft"] = time.perf_counter() - t_llm_start
                        first_token_received = True

                        # Capture token usage from streaming (if available)
                        if hasattr(chunk, 'x_groq') and chunk.x_groq and hasattr(chunk.x_groq, 'usage'):
                            usage = chunk.x_groq.usage
                            if PERFORMANCE_PROFILING and usage:
                                self.policy_engine.token_profiler.set_api_usage(
                                    usage.prompt_tokens, usage.completion_tokens
                                )
                    
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
                        "content": None,
                        "tool_calls": tool_calls,
                    })
                    
                    t_tool_start = time.perf_counter()
                    tool_results = await self._handle_tool_calls(tool_calls, policy_decision)
                    self.metrics["tools_latency"] = time.perf_counter() - t_tool_start

                    if PERFORMANCE_PROFILING:
                        self.policy_engine.token_profiler.set_tool_exec_latency(
                            self.metrics["tools_latency"] * 1000
                        )
                    
                    for tr in tool_results:
                        self.chat_history.append(tr)
                    
                    # Second LLM request (after tool execution)
                    # No tools exposed on the follow-up — it's a pure response generation
                    recent_history = self.chat_history[-20:] if len(self.chat_history) > 20 else self.chat_history
                    new_messages = [{"role": "system", "content": policy_decision.system_prompt}] + recent_history
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

                if PERFORMANCE_PROFILING:
                    self.policy_engine.token_profiler.set_llm_latency(
                        self.metrics["llm_total"] * 1000
                    )

            print("Generating streamed LLM response...")
            await self._stream_and_send(combined_stream_gen(), return_audio, policy_decision)
            
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

    async def _stream_and_send(self, stream_gen, return_audio: bool, policy_decision=None):
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

        # ── OUTPUT POLICY: Validate the response before sending ──────
        if full_response and policy_decision:
            validation = self.policy_engine.validate_output(
                full_response,
                rag_was_invoked=self.rag_invoked_this_turn,
            )

            if validation.was_modified:
                print(f">>> Output validation modified response. Violations: {validation.violations}")
                full_response = validation.sanitized_response

            # Update decision log with validation result
            if PERFORMANCE_PROFILING and policy_decision.decision_log:
                self.policy_engine.decision_logger.update_output_validation(
                    policy_decision.decision_log, validation,
                )
                # Re-print the updated log section
                if validation.violations:
                    print(f">>> Output Violations: {validation.violations}")

        if not self.is_interrupted:
            await self.websocket.send_json({"type": "response_complete", "text": full_response})
        
        if full_response:
            self.chat_history.append({"role": "assistant", "content": full_response})
            # Persist assistant message
            asyncio.create_task(self._persist_message("assistant", full_response))
        print(f"Finished response. Interrupted: {self.is_interrupted}")
        
        # ── Performance + Token Profiler Report ──────────────────────
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
            print(f" Conversation Stage:   {self.current_stage.value}")
            print("="*50)

            # Token Profiler
            report = self.policy_engine.token_profiler.generate_report()
            print(self.policy_engine.token_profiler.format_report(report))
