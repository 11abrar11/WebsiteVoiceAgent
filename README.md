# PP5 Media Solutions - AI Voice Agent

## 1. About the Project

This project is a production-quality **AI Voice Agent** integrated into the existing PP5 Media Solutions website. The objective is to create an intelligent system that acts like an experienced business consultant representing the company, rather than a conventional, scripted chatbot. 

It is built with clean architecture and robust engineering practices. The AI is designed to communicate naturally, while a deterministic backend securely handles core business logic, database transactions, and integrations via a lead-centric architecture.

---

## 2. What it Does

The AI Voice Agent seamlessly guides users through a comprehensive interaction flow:

- **Lead Identification:** Users authenticate and onboard via their email address before connecting, ensuring every conversation traces back to a stable business identity.
- **Consultative Conversation:** Answers questions about the company, understands specific user requirements, and asks intelligent follow-up questions.
- **Lead Qualification:** Evaluates potential clients and securely stores their structured profiles.
- **Meeting Booking:** Allows users to schedule available time slots directly during the conversation.
- **Continuous Context (Long-term Memory):** Leverages a `ContextBuilder` to remember past conversation summaries for returning leads, giving the AI context over multiple sessions.
- **Conversation Management:** Automatically stores full conversation histories, generates AI-powered summaries, and tracks operational metadata (duration, message counts, model used).
- **Escalation & Notification:** Escalates conversations when required and triggers email notifications to the company.
- **Analytics & Admin Dashboard:** Provides administrators with a dashboard to view real-time operations, manage meetings, and analyze AI performance.

---

## 3. Skills and Technologies Used

### **Frontend (Website)**
- **Framework:** React 18, Vite, TypeScript
- **Styling & UI:** Tailwind CSS, Radix UI (shadcn/ui accessible components)
- **Animations:** Framer Motion, Tailwind Animate
- **Routing & Forms:** Wouter, React Hook Form, Zod (Schema validation)
- **Data Visualization:** Recharts

### **Backend (Voice Agent API)**
- **Framework:** FastAPI (Python), Uvicorn
- **Real-Time Communication:** WebSockets (handling audio streams and real-time messaging)
- **Database:** PostgreSQL (with asyncpg driver), SQLAlchemy (ORM)
- **AI & LLM Services:** Groq API, LangChain Text Splitters
- **Audio Processing:** Faster-Whisper (Speech-to-Text), Kokoro (Text-to-Speech), Soundfile, Numpy
- **Vector Database (RAG):** Qdrant Client, Sentence-Transformers
- **Security:** Passlib (Bcrypt), Python-JOSE (Cryptography)

---

## 4. Architecture Diagrams

### Entity Relationship Diagram (Lead-Centric Database)

```mermaid
erDiagram
    LEADS {
        int id PK "Auto-increment"
        string email UK "UNIQUE NOT NULL"
        string company
        string lead_status
        float data_completeness
        datetime last_contacted
    }

    CONVERSATIONS {
        int id PK
        int lead_id FK "→ leads.id"
        ConversationStatus status
        float duration_seconds
        int message_count
        string model_used
    }

    MESSAGES {
        int id PK
        int conversation_id FK
        string speaker
        text content
    }

    CONVERSATION_SUMMARIES {
        int id PK
        int conversation_id FK, UK
        text summary
        int summary_version
        string summary_model
    }

    MEETINGS {
        int id PK
        int lead_id FK "→ leads.id"
        date date
        time time
        MeetingStatus status
    }

    LEADS ||--o{ CONVERSATIONS : "has many"
    LEADS ||--o{ MEETINGS : "has many"
    CONVERSATIONS ||--o{ MESSAGES : "has many"
    CONVERSATIONS ||--o| CONVERSATION_SUMMARIES : "has one"
```

### System Request Flow

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant WS as Voice Router
    participant LS as LeadService
    participant DB as PostgreSQL
    participant CM as ConversationManager
    participant CB as ContextBuilder

    FE->>FE: Normalize & Validate Email
    FE->>WS: Connect WS(?email=mohammed@example.com)
    WS->>LS: get_or_create_lead("mohammed@example.com")
    LS->>LS: Normalize & Validate
    LS->>DB: Lookup / Create Lead
    LS-->>WS: (lead_id=42, is_new)
    WS->>CM: init(websocket, lead_id=42)
    CM->>CB: build(lead_id=42)
    CB->>DB: Fetch profile + 3 recent summaries
    CB-->>CM: Formatted context string
    CM->>DB: create_conversation(lead_id=42)
    CM-->>FE: {"type": "ready"}
```

## 5. Conversation Policy Engine

The Conversation Policy Engine is a deterministic backend layer that owns business rules, conversation stages, tool gating, and output validation. It ensures the LLM acts solely as a reasoning and language engine, while the backend remains the absolute source of truth.

### Architecture Overview

```mermaid
graph TD
    subgraph "User Turn"
        A["User Message"] --> B["ConversationManager"]
    end

    subgraph "Policy Engine (Pre-LLM)"
        B --> PE["PolicyEngine.evaluate()"]
        PE --> SE["StageEngine"]
        PE --> TG["ToolGate"]
        PE --> MP["MeetingPolicy"]
        PE --> CS["ConversationStrategy"]
        PE --> PB["DynamicPromptBuilder"]
    end

    subgraph "LLM Request (Gated)"
        PB --> LLM["Groq API"]
        TG -->|"filtered tools"| LLM
        LLM --> RESP["LLM Response"]
    end

    subgraph "Output Policy (Post-LLM)"
        RESP --> EP["EnterprisePolicy"]
        EP --> VALID{"Valid?"}
        VALID -->|"Yes"| USER["Safe Response → User"]
        VALID -->|"Modified"| STRIP["Sanitize → User"]
    end

    subgraph "Debug (PERFORMANCE_PROFILING)"
        PE --> DL["DecisionLogger"]
        LLM --> TP["TokenProfiler"]
    end
```

### Stage Transition Flow

```mermaid
stateDiagram-v2
    [*] --> GREETING: turn 1

    GREETING --> DISCOVERY: user shares context
    GREETING --> KNOWLEDGE: asks about services

    DISCOVERY --> BUSINESS_DISCOVERY: mentions company/industry
    DISCOVERY --> KNOWLEDGE: asks about services
    DISCOVERY --> MEETING_DISCUSSION: wants to meet

    BUSINESS_DISCOVERY --> QUALIFICATION: budget/timeline discussed
    BUSINESS_DISCOVERY --> KNOWLEDGE: asks about services

    QUALIFICATION --> MEETING_DISCUSSION: ready to schedule
    QUALIFICATION --> KNOWLEDGE: asks about services

    KNOWLEDGE --> DISCOVERY: returns to needs discussion
    KNOWLEDGE --> MEETING_DISCUSSION: wants to meet

    MEETING_DISCUSSION --> MEETING_BOOKING: confirms a slot
    MEETING_DISCUSSION --> MEETING_RESCHEDULE: has active meeting

    MEETING_BOOKING --> CLOSING: booking complete
    MEETING_RESCHEDULE --> CLOSING: reschedule complete

    CLOSING --> [*]
```

### Token Profiling & Optimization
By moving from a monolithic static prompt to a **dynamic, stage-aware prompt** with gated tools and on-demand RAG, we achieved a **50-60% reduction in prompt tokens per turn** and eliminated LLM hallucinations regarding business rules.

### Robustness & Safety
- **Enterprise Policy:** Blocks the LLM from outputting internal system instructions, XML tags, or hallucinated pricing.
- **Meeting Policy:** Enforces a strict one-active-meeting-per-lead rule at the database level.
- **Tool Gating:** The LLM only sees the tools relevant to the current conversation stage.
