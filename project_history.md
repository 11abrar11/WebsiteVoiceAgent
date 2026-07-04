# PP5 Voice Agent — Full Project History & Architecture Guide

> Written as a senior engineer explaining every decision to a junior engineer.
> Last updated: 2026-06-30

---

## 1. What Are We Building?

An AI-powered **voice agent** embedded in the PP5 Media Solutions website. A user visits `http://localhost:5173/voice-agent`, clicks "Start Conversation," and has a **spoken, real-time conversation** with an AI that knows everything about PP5's services, pricing, and case studies.

The AI should feel like talking to a real human consultant — not a chatbot, not a robot reading bullet points.

---

## 2. The Tech Stack (and Why Each Piece Was Chosen)

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | React (Vite) + TypeScript | Already existed as the PP5 website. We added a `/voice-agent` page. |
| **Backend** | FastAPI (Python) | Async-native. WebSockets are first-class citizens. Python has the best ML/AI library ecosystem. |
| **Speech-to-Text (STT)** | `faster-whisper` (tiny.en model) | Runs locally on CPU. No API call latency. The `tiny.en` model is ~75MB, loads in seconds, and transcribes English audio fast. Trade-off: accuracy is lower than `base` or `small` models, but latency wins for voice agents. |
| **LLM** | Groq API (`llama-3.1-8b-instant`) | Groq runs LLMs on custom LPUs — inference is 10-50x faster than OpenAI. We chose `llama-3.1-8b-instant` because it's the fastest model on Groq. Trade-off: it's not as smart as GPT-4 or Llama 70B, but for a voice agent where you need sub-second token generation, speed beats intelligence. |
| **Text-to-Speech (TTS)** | Kokoro (`af_heart` voice) | Open-source, runs locally, surprisingly natural-sounding. No API costs. Trade-off: synthesis is CPU-bound and blocking — this is a current bottleneck (more on that below). |
| **Vector Database (RAG)** | Qdrant (Docker container) | Stores embeddings of the knowledge base. Lightweight, easy to self-host. |
| **Embedding Model** | `all-MiniLM-L6-v2` (sentence-transformers) | Fast, small (80MB), good enough for semantic search over a small knowledge base. |
| **Transport** | WebSocket | HTTP request/response doesn't work for streaming audio in both directions. WebSocket gives us a persistent, bidirectional channel. |

---

## 3. The Architecture (How Data Flows)

```
User speaks into mic
       ↓
[Browser: VAD detects silence → MediaRecorder stops → audio blob sent via WebSocket]
       ↓
[FastAPI WebSocket handler receives binary audio]
       ↓
[STT: faster-whisper transcribes audio → text]
       ↓
[RAG: Qdrant retrieves top 5 relevant knowledge base chunks]
       ↓
[LLM: Groq streams response token-by-token]
       ↓
[Sentence accumulator: waits for . ! ? to form complete sentences]
       ↓
[TTS: Kokoro synthesizes each sentence → WAV bytes]
       ↓
[WebSocket sends base64-encoded WAV + text chunk to browser]
       ↓
[Browser: Audio queue plays chunks sequentially]
       ↓
[When playback finishes → VAD restarts → cycle repeats]
```

---

## 4. Chronological History of Every Change

### Phase 1: Scaffolding (Initial Setup)

**What was done:**
- Created the FastAPI project structure under `voice-agent/`
- Set up `docker-compose.yml` with PostgreSQL (for future conversation persistence) and Qdrant
- Created the knowledge base directory with 6 markdown files: `services.md`, `company_overview.md`, `faqs.md`, `case_studies.md`, `pricing_guidelines.md`, `contact_information.md`
- Built the RAG ingestion script (`app/rag/ingest.py`) that splits markdown files into chunks, embeds them with `all-MiniLM-L6-v2`, and stores them in Qdrant
- Built the retriever (`app/rag/retriever.py`) that takes a query, embeds it, and returns the top-k most similar chunks

**Original parameters:**
- `chunk_size=500`, `chunk_overlap=50` in the text splitter
- `top_k=2` in the retriever (only fetched 2 chunks)

### Phase 2: Core AI Pipeline

**What was done:**
- Integrated `faster-whisper` for STT ([stt.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/stt.py))
- Integrated Groq API for LLM ([llm.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/llm.py))
- Integrated Kokoro for TTS ([tts.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/tts.py))
- Built the `ConversationManager` class that orchestrates the full pipeline
- Created the WebSocket endpoint at `/api/voice/stream`

**Original behavior:** Everything was **synchronous and blocking**:
1. Wait for ENTIRE audio from user
2. Transcribe ALL of it
3. Retrieve RAG context
4. Generate the ENTIRE LLM response (not streamed)
5. Synthesize the ENTIRE response as one big WAV
6. Send the ENTIRE WAV back

**Why this was bad:** Steps 4 and 5 combined took ~8-10 seconds. The user sat there watching a loading spinner for 10 seconds before hearing anything.

### Phase 3: Frontend (VoiceAgent.tsx)

**What was done:**
- Created the React page at [VoiceAgent.tsx](file:///c:/Projects/Website%20Voice%20Agent/Website/client/src/pages/VoiceAgent.tsx)
- Used `MediaRecorder` API to capture microphone audio
- WebSocket connection to the backend

**Original behavior:** "Push-to-talk" — user clicks a button to start recording, clicks again to stop. This felt unnatural.

### Phase 4: Connection Bug (Recurring Issue)

**The problem:** When you click "Start Conversation," the WebSocket connects, sends the greeting, and then the greeting's TTS audio is so large that it either exceeds WebSocket frame limits or takes so long to synthesize that the connection times out. The frontend shows "Connecting..." and then snaps back to "Start Conversation."

**The server logs confirm this pattern:**
```
connection open
connection closed
connection open
connection closed
```
Over and over. The WebSocket connects, the server tries to send the greeting audio, something fails, and the connection drops.

**Root cause (most likely):** The `send_greeting()` method was synthesizing the ENTIRE greeting (~40 words) as a single WAV blob. Kokoro takes several seconds to synthesize that. During that time, the WebSocket may be timing out or the browser may be closing it because no messages are being received.

**Fix applied:** Split the greeting into 3 smaller sentences, synthesize and send each one individually. This way the first audio chunk arrives in <1 second.

> [!WARNING]
> **This bug may still be present.** The logs from the last run still show rapid `connection open / connection closed` cycles. The `chat_history` attribute is missing from `__init__` (it was accidentally removed during an edit — see Known Bugs below). This would cause an `AttributeError` on the very first `send_greeting()` call, killing the WebSocket connection instantly.

### Phase 5: Latency Fix — LLM Streaming

**The problem:** User reported ~10 second delay between asking a question and hearing the response.

**What was done:**
- Added `generate_response_stream()` method to [llm.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/llm.py) that uses `stream=True` with the Groq API
- This yields tokens as they arrive instead of waiting for the full response
- In `conversation_manager.py`, we now accumulate tokens into complete sentences (split on `. ! ?`), and as soon as a sentence is complete, we synthesize it with Kokoro and send the audio immediately

**Why this helps:** Instead of waiting 3s for LLM + 5s for TTS on the full paragraph, we now wait ~0.5s for the first sentence from the LLM + ~1s for Kokoro to synthesize that one sentence = **~1.5s to first audio**. The remaining sentences stream in while the first one is playing.

**Parameters changed:**
| Parameter | Before | After | Why |
|-----------|--------|-------|-----|
| `llm.py: max_tokens` (streaming) | N/A | `512` | Allows longer responses in streaming mode |
| `llm.py: stream` | `False` | `True` (in new method) | Core latency fix |

### Phase 6: Voice Activity Detection (VAD)

**The problem:** User said "I don't want click to start / click to listen. I want natural conversation."

**What was done in [VoiceAgent.tsx](file:///c:/Projects/Website%20Voice%20Agent/Website/client/src/pages/VoiceAgent.tsx):**
- Created an `AudioContext` + `AnalyserNode` that continuously monitors microphone volume
- When volume exceeds `SILENCE_THRESHOLD = 15`, we consider the user to be speaking
- When volume drops below threshold for `SILENCE_DURATION = 1500ms` (1.5 seconds), we consider them done and auto-send the audio
- The `MediaRecorder` runs with `timeslice=250ms` so audio chunks are buffered in real-time

**Trade-offs and tunable parameters:**
| Parameter | Value | What it does |
|-----------|-------|-------------|
| `SILENCE_THRESHOLD` | `15` | Average frequency amplitude that counts as "speech." Lower = more sensitive (picks up background noise). Higher = needs louder speech. |
| `SILENCE_DURATION` | `1500` (ms) | How long the user must be silent before we consider them "done." Shorter = faster but might cut off mid-thought pauses. Longer = safer but adds latency. |
| `analyser.fftSize` | `256` | Resolution of frequency analysis. Larger = more accurate but slower. 256 is fast enough for VAD. |

### Phase 7: Audio Playback Queue

**The problem:** Since we now stream multiple audio chunks (one per sentence), they could overlap if played simultaneously.

**What was done:**
- Built an audio queue in the frontend (`audioQueueRef`)
- Each incoming audio chunk is pushed to the queue
- `playNextInQueue()` plays one at a time, advancing to the next `onended`
- When the queue is empty, the state returns to `idle` and recording restarts

### Phase 8: RAG Quality Fix

**The problem:** User asked "What are your services?" and the AI responded with generic fluff about "24/7 availability" instead of listing the actual services (Graphic Design, Animation, Digitization, BPO).

**Root cause investigation:**
I ran a test script (`test_rag.py`) that queried "What are your services?" and printed what the vector database returned. The results were:
1. A chunk from `faqs.md` about working hours (24x5 support)
2. A chunk from `faqs.md` about industries served
3. A chunk from `company_overview.md` about service strengths

The actual services list from `services.md` wasn't in the top results because:
- `services.md` started with the heading `# Capabilities` (not "Services"), so the embedding was semantically distant from the query "what are your services"
- The `chunk_size=500` was chopping the services list into fragments, so no single chunk contained a complete answer

**Fixes applied:**

1. **Rewrote the top of `services.md`**: Changed heading from `# Capabilities` to `# PP5 Media Solutions Services` and added a clear summary paragraph listing all 4 service domains
2. **Increased `chunk_size` from 500 to 1500** in `ingest.py`: This keeps entire sections together so the embedding captures the full meaning
3. **Increased `chunk_overlap` from 50 to 150**: More overlap means less chance of losing context at chunk boundaries
4. **Increased `top_k` from 2 to 5** in `conversation_manager.py`: Retrieves 5 chunks instead of 2, giving the LLM more material to select the right answer from

**Trade-off of larger chunks:** The LLM now receives more context per chunk, which means it could generate longer responses. This was later addressed by adding "EXTREME BREVITY" to the system prompt.

### Phase 9: TTS Speed and Naturalness

**The problem:** User said "It is speaking very slow because there are no signs of natural language. It says that a robot is speaking."

**Fixes applied:**

1. **TTS speed: `1.0` → `1.2`** in [tts.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/tts.py): Kokoro's default speed of 1.0 sounds deliberately paced, like an audiobook narrator. 1.2 sounds more like normal conversational speed.

2. **System prompt rewrite** in [conversation_manager.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/conversation_manager.py): Instructed the LLM to use contractions, fillers, short sentences, and casual language.

3. **Hardcoded filler words** (e.g., "Hmm..."): Initially I added code that immediately synthesized a random filler word ("Hmm...", "Let's see...", "Right,", "Well...") and sent it before the LLM even started. The idea was to provide instant audio feedback while the LLM was thinking.

**User feedback on fillers:** User said the hardcoded fillers felt unnatural — they were separate from the actual response. User preferred the LLM itself to generate fillers naturally as part of its response.

**Fix:** Removed the hardcoded filler audio code. Updated the system prompt to tell the LLM: *"Generate your own natural pauses and filler words at the start of your sentences."*

### Phase 10: Response Length

**The problem:** After increasing chunk size to 1500, the LLM started giving very long responses — reciting entire blocks from the knowledge base. This is terrible for a voice agent where conciseness is critical.

**Fix:** Added `"EXTREME BREVITY: Your answers must be incredibly short, precise, and accurate. Give exactly the information requested in 1 or 2 sentences max."` to the system prompt.

### Phase 11: User-First Interaction & VAD Rewrite

**The problem:** The user wanted the agent to start in a listening state without automatically greeting the user, and wanted the microphone button to act as a proper pause/resume toggle that forced an immediate response if paused mid-speech. Additionally, the single-sentence LLM streaming caused unnatural gaps.

**What was done:**
- **Backend Refactor**: Removed `send_greeting()` entirely. Added a `ready` WebSocket signal so the frontend knows when to start listening. 
- **Frontend Rewrite**: Rewrote `VoiceAgent.tsx` to handle state transitions accurately using React `useRef` for variables in the animation loop. The microphone button now truly pauses the VAD and flushes any active recording immediately.
- **2-Sentence Batching**: Updated `conversation_manager.py` to collect at least 2 sentences before dispatching to Kokoro TTS, drastically improving the natural flow and reducing perceived latency.

### Phase 12: Advanced Session, Low-Latency Tooling, & Email Integration

**The problem:** High latency due to PostgreSQL integration and double API calls, meetings not saving correctly due to time formatting, missing session continuity, and no notification system.

**What was done:**
- **Streaming Tool Calls:** Refactored LLM processing to consume tools seamlessly during the stream instead of a blocking, two-step process.
- **Async Threading for RAG:** `rag_retriever.retrieve` was causing synchronous blocking during Postgres queries. Wrapped it in `asyncio.to_thread`.
- **Faster TTS Rendering:** Dropped the sentence chunk buffer from 2 sentences to 1, cutting Time-To-First-Byte in half.
- **Robust Meeting Parsing:** Integrated `dateutil.parser` in the meeting engine to correctly handle all LLM time outputs, fixing the booking failure.
- **Email Integration:** Added `app/email/sender.py` to trigger Gmail SMTP notifications whenever a meeting is booked.
- **Session Hierarchy:** Decoupled `visitor_id` and `conversation_id`. The React client generates `visitor_id` and passes it to the WebSocket, allowing proper user tracking across drops and reconnects without leaking data.
- **Identity & Follow-Ups:** System prompt heavily locked down to prohibit fake AI names, prohibit asking redundant questions, and mandate a follow-up question on every turn.

### Phase 13: Tool-Calling Robustness & XML Leakage Fix

**The problem:** 
1. Tool calls like `update_lead_info` were executing in the background, but the conversation was silently aborting and dropping the turn, leading to an awkward silence or generic "I encountered an error" message.
2. The AI was occasionally leaking XML function tags (e.g., `<function.update_lead_info>`) in its spoken response instead of executing them natively.

**What was done:**
- **Fixed `tc.id` Regression:** During the Phase 12 streaming transition, the manual tool-call accumulator built dictionaries, but the loop attempted to access `tc.id` via dot notation. This caused a silent `AttributeError` right after the tool executed, killing the turn before the second LLM generation. Updated to use the safely extracted `tc_id`.
- **System Prompt Refactor:** Removed negative constraints (`NEVER use raw XML tags like <function>`) which were inadvertently teaching the model the wrong syntax ("Pink Elephant" problem). Added a positive constraint: `"When using tools like update_lead_info or book_meeting, you must use the native JSON tool calling API. Do not embed JSON, code, or tool commands in your conversational speech."`
- **End-to-End Validation:** The tool loop is now fully closed. The AI updates the DB natively and flawlessly generates contextual replies like *"I've made a note of your name, what's your email?"* without exposing XML.


### Phase 13: Tool-Calling Robustness & XML Leakage Fix

**The problem:** 
1. Tool calls like `update_lead_info` were executing in the background, but the conversation was silently aborting and dropping the turn, leading to an awkward silence or generic "I encountered an error" message.
2. The AI was occasionally leaking XML function tags (e.g., `<function.update_lead_info>`) in its spoken response instead of executing them natively.

**What was done:**
- **Fixed `tc.id` Regression:** During the Phase 12 streaming transition, the manual tool-call accumulator built dictionaries, but the loop attempted to access `tc.id` via dot notation. This caused a silent `AttributeError` right after the tool executed, killing the turn before the second LLM generation. Updated to use the safely extracted `tc_id`.
- **System Prompt Refactor:** Removed negative constraints (`NEVER use raw XML tags like <function>`) which were inadvertently teaching the model the wrong syntax ("Pink Elephant" problem). Added a positive constraint: `"When using tools like update_lead_info or book_meeting, you must use the native JSON tool calling API. Do not embed JSON, code, or tool commands in your conversational speech."`
- **End-to-End Validation:** The tool loop is now fully closed. The AI updates the DB natively and flawlessly generates contextual replies like *"I've made a note of your name, what's your email?"* without exposing XML.


### Phase 11: User-First Interaction & VAD Rewrite

**The problem:** The user wanted the agent to start in a listening state without automatically greeting the user, and wanted the microphone button to act as a proper pause/resume toggle that forced an immediate response if paused mid-speech. Additionally, the single-sentence LLM streaming caused unnatural gaps.

**What was done:**
- **Backend Refactor**: Removed `send_greeting()` entirely. Added a `ready` WebSocket signal so the frontend knows when to start listening. 
- **Frontend Rewrite**: Rewrote `VoiceAgent.tsx` to handle state transitions accurately using React `useRef` for variables in the animation loop. The microphone button now truly pauses the VAD and flushes any active recording immediately.
- **2-Sentence Batching**: Updated `conversation_manager.py` to collect at least 2 sentences before dispatching to Kokoro TTS, drastically improving the natural flow and reducing perceived latency.

### Phase 12: Advanced Session, Low-Latency Tooling, & Email Integration

**The problem:** High latency due to PostgreSQL integration and double API calls, meetings not saving correctly due to time formatting, missing session continuity, and no notification system.

**What was done:**
- **Streaming Tool Calls:** Refactored LLM processing to consume tools seamlessly during the stream instead of a blocking, two-step process.
- **Async Threading for RAG:** `rag_retriever.retrieve` was causing synchronous blocking during Postgres queries. Wrapped it in `asyncio.to_thread`.
- **Faster TTS Rendering:** Dropped the sentence chunk buffer from 2 sentences to 1, cutting Time-To-First-Byte in half.
- **Robust Meeting Parsing:** Integrated `dateutil.parser` in the meeting engine to correctly handle all LLM time outputs, fixing the booking failure.
- **Email Integration:** Added `app/email/sender.py` to trigger Gmail SMTP notifications whenever a meeting is booked.
- **Session Hierarchy:** Decoupled `visitor_id` and `conversation_id`. The React client generates `visitor_id` and passes it to the WebSocket, allowing proper user tracking across drops and reconnects without leaking data.
- **Identity & Follow-Ups:** System prompt heavily locked down to prohibit fake AI names, prohibit asking redundant questions, and mandate a follow-up question on every turn.

### Phase 13: Tool-Calling Robustness & XML Leakage Fix

**The problem:** 
1. Tool calls like `update_lead_info` were executing in the background, but the conversation was silently aborting and dropping the turn, leading to an awkward silence or generic "I encountered an error" message.
2. The AI was occasionally leaking XML function tags (e.g., `<function.update_lead_info>`) in its spoken response instead of executing them natively.

**What was done:**
- **Fixed `tc.id` Regression:** During the Phase 12 streaming transition, the manual tool-call accumulator built dictionaries, but the loop attempted to access `tc.id` via dot notation. This caused a silent `AttributeError` right after the tool executed, killing the turn before the second LLM generation. Updated to use the safely extracted `tc_id`.
- **System Prompt Refactor:** Removed negative constraints (`NEVER use raw XML tags like <function>`) which were inadvertently teaching the model the wrong syntax ("Pink Elephant" problem). Added a positive constraint: `"When using tools like update_lead_info or book_meeting, you must use the native JSON tool calling API. Do not embed JSON, code, or tool commands in your conversational speech."`
- **End-to-End Validation:** The tool loop is now fully closed. The AI updates the DB natively and flawlessly generates contextual replies like *"I've made a note of your name, what's your email?"* without exposing XML.


---

## 5. Current State of All Parameters

### Backend Parameters

| File | Parameter | Current Value | Purpose |
|------|-----------|---------------|---------|
| [llm.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/llm.py) | `model` | `llama-3.1-8b-instant` | Fastest model on Groq |
| [llm.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/llm.py) | `temperature` | `0.7` | Controls randomness. 0.7 = fairly creative but not wild |
| [llm.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/llm.py) | `max_tokens` (non-stream) | `256` | Legacy method, rarely used now |
| [llm.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/llm.py) | `max_tokens` (stream) | `512` | Max response length for streaming |
| [tts.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/tts.py) | `voice` | `af_heart` | Kokoro voice preset (American female) |
| [tts.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/tts.py) | `speed` | `1.2` | Speaking rate (1.0 = default, 1.2 = conversational) |
| [tts.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/tts.py) | `sample_rate` | `24000` Hz | Kokoro's native sample rate |
| [stt.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/stt.py) | `model_size` | `tiny.en` | Smallest English-only Whisper model |
| [stt.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/stt.py) | `device` | `cpu` | No GPU used |
| [stt.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/stt.py) | `compute_type` | `int8` | Quantized for speed on CPU |
| [stt.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/stt.py) | `beam_size` | `5` | Beam search width for transcription accuracy |
| [ingest.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/rag/ingest.py) | `chunk_size` | `1500` | Characters per knowledge base chunk |
| [ingest.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/rag/ingest.py) | `chunk_overlap` | `150` | Overlap between adjacent chunks |
| [ingest.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/rag/ingest.py) | `embedding_model` | `all-MiniLM-L6-v2` | 384-dimension embeddings |
| [conversation_manager.py](file:///c:/Projects/Website%20Voice%20Agent/voice-agent/app/services/conversation_manager.py) | `top_k` | `5` | Number of RAG chunks retrieved per query |

### Frontend Parameters

| File | Parameter | Current Value | Purpose |
|------|-----------|---------------|---------|
| [VoiceAgent.tsx](file:///c:/Projects/Website%20Voice%20Agent/Website/client/src/pages/VoiceAgent.tsx) | `SILENCE_THRESHOLD` | `15` | VAD sensitivity (average freq amplitude) |
| [VoiceAgent.tsx](file:///c:/Projects/Website%20Voice%20Agent/Website/client/src/pages/VoiceAgent.tsx) | `SILENCE_DURATION` | `1500` ms | How long silence = "done speaking" |
| [VoiceAgent.tsx](file:///c:/Projects/Website%20Voice%20Agent/Website/client/src/pages/VoiceAgent.tsx) | `fftSize` | `256` | Frequency analysis resolution |
| [VoiceAgent.tsx](file:///c:/Projects/Website%20Voice%20Agent/Website/client/src/pages/VoiceAgent.tsx) | `MediaRecorder timeslice` | `250` ms | How often audio data is buffered |
| [VoiceAgent.tsx](file:///c:/Projects/Website%20Voice%20Agent/Website/client/src/pages/VoiceAgent.tsx) | WebSocket URL | `ws://127.0.0.1:8000/api/voice/stream` | Backend endpoint |

---

## 6. Known Bugs (As of Right Now)

*None currently known. Bug #1 (chat_history not initialized) and Bug #2 (WebSocket drops on connect) were fully fixed during Phase 11.*

---

## 7. Current System Prompt (Full Text)

```
You are a friendly, natural-sounding voice consultant for PP5 Media Solutions. You are on a live voice call with a potential client. 
VOICE CONVERSATION RULES:
1. BREVITY: Keep answers to 2-3 short sentences. Be precise and accurate. Never ramble.
2. NATURAL SPEECH: Speak like a real human consultant on a phone call. Use a polite, conversational tone but remain concise and professional. DO NOT use filler words like 'um' or 'uh'.
3. PACING: Use commas for natural breathing pauses. Use exclamation marks when enthusiastic. Speak casually with contractions like 'we're', 'it's', 'you'll', 'that's'.
4. Answer strictly from the provided context. Do not drift away from company details.
5. HARD RULE: Protect all internal lead data and company secrets. If asked for proprietary data, gracefully decline.
6. LEAD COLLECTION: Your goal is to collect the client's Name, Email, Phone number, Company name, and Project Needs. Ask for these pieces of information naturally, ONE AT A TIME. Whenever you receive a piece of information, immediately call the `update_lead_info` tool.
7. No markdown formatting whatsoever.
8. MEETINGS: If the user wants to schedule a meeting or talk to someone, use the get_available_meeting_times tool first, then present the options naturally. After the user picks a time, use the book_meeting tool.
9. TOOL EXECUTION: When using tools like update_lead_info or book_meeting, you must use the native JSON tool calling API. Do not embed JSON, code, or tool commands in your conversational speech.
10. IDENTITY: You are an unnamed AI voice consultant for PP5 Media Solutions. DO NOT introduce yourself with a human name.
```

---

## 8. File Structure

```
c:\Projects\Website Voice Agent\
├── knowledge_base/                    # Raw markdown files about PP5
│   ├── services.md                    # Core services (edited for RAG)
│   ├── company_overview.md
│   ├── faqs.md
│   ├── case_studies.md
│   ├── pricing_guidelines.md
│   └── contact_information.md
│
├── voice-agent/                       # Python backend
│   ├── main.py                        # FastAPI app entry point
│   ├── requirements.txt               # Python dependencies
│   ├── docker-compose.yml             # PostgreSQL + Qdrant
│   ├── .env                           # GROQ_API_KEY
│   └── app/
│       ├── services/
│       │   ├── conversation_manager.py # Orchestrates STT→RAG→LLM→TTS pipeline
│       │   ├── llm.py                 # Groq API (streaming + non-streaming)
│       │   ├── tts.py                 # Kokoro TTS synthesis
│       │   └── stt.py                 # faster-whisper transcription
│       ├── rag/
│       │   ├── ingest.py              # Loads markdown → Qdrant
│       │   └── retriever.py           # Queries Qdrant for context
│       └── routers/
│           └── voice.py               # WebSocket endpoint
│
└── Website/client/                    # React frontend (Vite)
    └── src/pages/
        └── VoiceAgent.tsx             # Voice agent UI + VAD + audio queue
```

---

## 9. What Has NOT Been Built Yet

| Feature | Status | Notes |
|---------|--------|-------|
| PostgreSQL conversation persistence | ✅ Completed | AsyncSessionLocal with SQLAlchemy integrated. |
| Meeting scheduling | ✅ Completed | Fully functional in `app/meeting/` |
| Email integration | 🚧 Pending | Directory `app/email/` exists. Gmail SMTP logic needs to be finalized. |
| One-log-per-session | 🚧 Pending | Need to consolidate logs for multiple conversations from the same `visitor_id` into a single, cohesive log entry. |
| Google Sheets integration | Not started | Directory `app/sheets/` exists but is empty |
| Lead scoring | Not started | Directory `app/scoring/` exists but is empty |
| Authentication/Dashboard | Not started | Directories exist but are empty |

---

## 10. What Needs to Happen Next

1. **Email Integration:** Finish the implementation of `app/email/sender.py` so that meeting notifications are actually dispatched via Gmail SMTP.
2. **One-log-per-session:** Consolidate server logs so that multiple conversation attempts from a single visitor are tracked cohesively.
