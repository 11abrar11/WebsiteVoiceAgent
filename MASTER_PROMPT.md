\# PP5 Media Solutions - AI Voice Agent (Master Development Specification)



> \*\*Version:\*\* 1.0

>

> \*\*Status:\*\* Development

>

> \*\*Primary Goal:\*\* Build a production-quality AI Voice Agent that integrates into the existing PP5 Media Solutions website while preserving the existing codebase and user experience.



\---



\# 1. Project Vision



You are an expert AI Software Engineer responsible for building a production-quality AI Voice Agent.



This is \*\*NOT\*\* a prototype.



This project should be developed using clean architecture, modular code, proper engineering practices, deterministic backend logic, and production-ready folder structures.



The objective is to create an AI Voice Agent that behaves like an experienced business consultant rather than a chatbot.



The AI should communicate naturally while the backend remains responsible for every deterministic business decision.



The Voice Agent should:



\* Answer questions regarding the company.

\* Understand user requirements.

\* Ask intelligent follow-up questions.

\* Qualify leads.

\* Book meetings.

\* Store conversation history.

\* Escalate conversations when required.

\* Generate summaries.

\* Update Google Sheets.

\* Notify the company through email.

\* Maintain complete conversation history.



The AI should never behave like a scripted FAQ bot.



It should behave like a knowledgeable consultant representing the company.



\---



\# 2. Existing Project



The existing website already exists.



DO NOT recreate it.



DO NOT redesign it.



DO NOT replace any UI.



DO NOT restructure the project unless absolutely necessary.



Instead,



Analyze the existing website first.



Understand:



\* Folder structure

\* Existing routing

\* Existing components

\* Existing styling

\* Existing color palette

\* Existing typography

\* Existing animations

\* Existing responsiveness

\* Existing dependencies



Only after understanding the project should any code be written.



\---



\# 3. Existing Website Rules



The existing website is the source of truth.



The Voice Agent must integrate naturally into it.



Only add:



```

/voice-agent

```



Reuse existing:



\* Components

\* Theme

\* Buttons

\* Cards

\* Fonts

\* Colors

\* Icons

\* Responsive behaviour



The Voice Agent page should feel like it was originally designed as part of the website.



It must never look like a separate application.



\---



\# 4. Development Philosophy



Always follow these principles.



\## Rule 1



Never rewrite working code.



\---



\## Rule 2



Never modify existing pages unless absolutely necessary.



\---



\## Rule 3



Never introduce unnecessary complexity.



\---



\## Rule 4



Prefer deterministic backend logic over LLM reasoning.



\---



\## Rule 5



Prefer modular code.



\---



\## Rule 6



Every module must have a single responsibility.



\---



\## Rule 7



Never duplicate business logic.



\---



\## Rule 8



Every feature must be testable independently.



\---



\## Rule 9



Every module should be replaceable without affecting the rest of the system.



\---



\## Rule 10



Always explain architectural decisions before implementing major changes.



\---



\# 5. Local Development Environment



This project is currently built entirely on the developer's local machine.



DO NOT assume cloud deployment.



DO NOT assume VPS deployment.



Everything should work locally.



Current architecture:



\* Existing Website

\* Docker Compose

\* FastAPI

\* PostgreSQL

\* Qdrant

\* Whisper

\* Kokoro

\* Groq API



Later this project may be migrated to a VPS.



Do not optimize for VPS today.



Optimize for maintainability and correctness.



\---



\# 6. High-Level Architecture



```

Existing Website

&#x20;       │

&#x20;       ▼

Voice Agent Page

&#x20;       │

&#x20;       ▼

Browser Microphone

&#x20;       │

&#x20;       ▼

Speech-To-Text

(Whisper)

&#x20;       │

&#x20;       ▼

Conversation Manager

&#x20;       │

&#x20;       ▼

LLM

(Groq)

&#x20;       │

&#x20;       ▼

Tool Calling

&#x20;       │

&#x20;┌──────┼──────────────┐

&#x20;▼      ▼              ▼

RAG   Lead Engine   Meeting Engine

&#x20;│        │              │

&#x20;▼        ▼              ▼

Qdrant PostgreSQL Google Sheets

&#x20;               │

&#x20;               ▼

&#x20;        Email Notification

&#x20;               │

&#x20;               ▼

&#x20;       Admin Dashboard

```



\---



\# 7. Technology Stack



Frontend



\* Existing Website

\* Reuse current framework

\* Existing design system



Backend



\* FastAPI



Database



\* PostgreSQL



Vector Database



\* Qdrant



Speech-To-Text



\* faster-whisper



Large Language Model



\* Groq API



Text-To-Speech



\* Kokoro



Lead Storage



\* Google Sheets



Authentication



\* JWT



Email



\* Existing email implementation



Containerization



\* Docker Compose



\---



\# 8. Folder Structure



Maintain a clean architecture.



Example:



```

voice-agent/



├── app/

│

├── api/

│

├── routers/

│

├── services/

│

├── rag/

│

├── prompts/

│

├── database/

│

├── models/

│

├── schemas/

│

├── repositories/

│

├── tools/

│

├── scoring/

│

├── meeting/

│

├── sheets/

│

├── email/

│

├── auth/

│

├── dashboard/

│

├── websocket/

│

├── utils/

│

├── config/

│

├── docker/

│

└── tests/

```



Keep business logic separated.



No giant files.



\---



\# 9. Knowledge Base



The knowledge base will be provided as Markdown files.



Examples:



```

knowledge-base/



about-company.md



services.md



pricing.md



faq.md



portfolio.md



case-studies.md

```



These Markdown files are the source of truth.



Never hardcode company knowledge.



Whenever company information changes, updating the Markdown files should automatically update the AI's knowledge after re-indexing.



\---



\# 10. RAG



Reuse the existing RAG architecture.



Reuse the existing Qdrant setup.



Create a separate Qdrant collection specifically for this Voice Agent project.



Do NOT share runtime state with the WhatsApp chatbot.



The Markdown knowledge base may be shared.



Each project should own its own vector collection.



\---



\# 11. Important Design Rule



The LLM is NOT the application.



The LLM is only one component.



The backend is the real application.



The LLM must NEVER:



\* calculate lead scores

\* decide lead categories

\* decide escalation logic

\* schedule meetings directly

\* write to databases

\* update Google Sheets

\* send emails

\* authenticate users

\* make business decisions



Instead,



The LLM should:



\* converse naturally

\* answer using RAG

\* ask follow-up questions

\* understand user intent

\* produce structured outputs

\* request backend tool calls



Everything else must be deterministic backend logic.



\---



\# 12. Development Workflow



Never attempt to build the entire project in one step.



Always work incrementally.



Every milestone should:



1\. Compile successfully.

2\. Run successfully.

3\. Be manually tested.

4\. Be documented.

5\. Be committed before moving to the next milestone.



Do not continue implementing new features until the current milestone is stable.



\# 13. Frontend Philosophy



The Voice Agent should not feel like an AI demo.



It should feel like a premium consultant sitting on the company's website.



The user should immediately understand:



\* what the assistant does,

\* what it can help with,

\* how to start talking,

\* and what will happen during the conversation.



The page should remain clean and minimal.



Avoid clutter.



\---



\# 14. Voice Agent Page



Create a dedicated route.



```

/voice-agent

```



Do not create a separate application.



This page must integrate naturally with the existing website.



Reuse:



\* Navigation Bar

\* Footer

\* Theme

\* Typography

\* Color Palette

\* Responsive Layout

\* Existing Components



\---



\# 15. Page Layout



Suggested structure



```

\-----------------------------------------



Navigation



\-----------------------------------------



Hero



"Talk with our AI Consultant"



Short description



Start Conversation Button



\-----------------------------------------



Voice Interface



Microphone



Connection Status



Current Conversation Status



Live Transcript



AI Response



\-----------------------------------------



Footer



\-----------------------------------------

```



No unnecessary widgets.



No dashboards.



No analytics.



No debug panels.



\---



\# 16. Initial User Experience



When the page loads:



The assistant should introduce itself.



Example behaviour:



> Hello!

>

> I'm the AI consultant for PP5 Media Solutions.

>

> I can help answer questions about our services, understand your requirements, and if you'd like, schedule a meeting with our team.

>

> Whenever you're ready, press the microphone button and start speaking.



The wording may change.



The behaviour should remain the same.



\---



\# 17. Conversation Style



The assistant should sound:



\* Professional

\* Friendly

\* Calm

\* Patient

\* Curious

\* Helpful



Avoid:



\* Robotic responses

\* Very long paragraphs

\* Repetitive phrases

\* Excessive enthusiasm

\* Corporate jargon



Never sound scripted.



\---



\# 18. Natural Conversation Rules



The assistant should naturally use:



small pauses



short acknowledgements



confirmation phrases



Examples



"Hmm..."



"I understand."



"That makes sense."



"Let me ask one more question."



"Got it."



"I appreciate the clarification."



Do NOT overuse fillers.



Do not add "um" or "uh" randomly.



Only use conversational acknowledgements where appropriate.



\---



\# 19. Interruptions (Barge-In)



This is mandatory.



If the assistant is speaking and the user begins speaking:



Immediately stop speech synthesis.



Start listening.



Process the user's interruption.



Continue naturally.



The assistant should never continue talking over the user.



\---



\# 20. Streaming



The experience should feel real-time.



Avoid:



```

Speak



↓



Wait 6 seconds



↓



Entire response

```



Prefer:



```

Speak



↓



Partial transcription



↓



LLM



↓



Streaming response



↓



Streaming speech

```



The objective is to minimize perceived latency.



\---



\# 21. Conversation Memory



The assistant must remember everything said during the current conversation.



Example



User:



"I'm from Bangalore."



Ten minutes later



Assistant:



"Since you're based in Bangalore..."



Do not repeatedly ask for the same information.



\---



\# 22. Conversation Manager



Create a dedicated Conversation Manager.



The Conversation Manager is responsible for:



\* conversation state

\* missing fields

\* tool execution

\* follow-up logic

\* interruption handling

\* conversation completion

\* conversation summary generation



The LLM should not manage application state.



The Conversation Manager should.



\---



\# 23. Conversation States



Suggested states



```

Greeting



↓



Discovery



↓



Qualification



↓



Information Collection



↓



Meeting Offer



↓



Meeting Scheduling



↓



Confirmation



↓



Summary



↓



Completed

```



The assistant should move naturally between these states.



\---



\# 24. Discovery Phase



The assistant should first understand why the user visited.



Examples



"I need a website."



"I need AI automation."



"I need marketing."



"I want WhatsApp automation."



"I need an AI chatbot."



The assistant should identify:



Primary Goal



before asking business questions.



\---



\# 25. Follow-Up Questions



Never ask every question immediately.



Bad



```

Name?



Phone?



Business?



Budget?



Timeline?



Company Size?



```



Good



```

User



↓



Requirement



↓



Clarification



↓



Business Context



↓



Timeline



↓



Decision Maker



↓



Budget



↓



Contact Information

```



The conversation should feel natural.



\---



\# 26. Information Collection



The assistant should gradually collect



Name



Phone



Email



Business



Industry



Requirement



Monthly Leads



Company Size



Timeline



Decision Maker



Budget



without making the user feel like they are completing a form.



\---



\# 27. Missing Information Tracking



Maintain a structured lead object.



Example



```

Name



Phone



Business



Industry



Requirement



Monthly Leads



Company Size



Budget



Timeline



Decision Maker

```



Unknown values remain NULL.



Each new answer updates only the relevant fields.



\---



\# 28. Data Completeness



Maintain a percentage.



Example



```

Business ✓



Industry ✓



Timeline ✗



Budget ✗



Decision Maker ✓

```



Result



```

Data Completeness



60%

```



Recalculate after every update.



This is separate from Lead Score.



\---



\# 29. Asking Intelligent Questions



Only ask questions whose answers are currently missing.



Never ask for information already known.



The Conversation Manager decides which field is missing next.



\---



\# 30. Clarification



If an answer is vague:



Ask a clarification question.



Example



User



"I need automation."



Assistant



"Certainly.



Are you referring to marketing automation, customer support automation, AI agents, or an internal workflow?"



\---



\# 31. Confidence



If the assistant is uncertain:



Ask another question.



Do NOT guess.



Do NOT hallucinate.



\---



\# 32. RAG Usage



Company knowledge must come only from RAG.



Never fabricate



\* services

\* portfolio

\* pricing

\* case studies

\* policies



If the answer cannot be found,



say so naturally,



then offer escalation if appropriate.



\---



\# 33. Escalation Behaviour



When escalation is required,



the assistant should respond naturally.



Example



"That's a great question.



I'd rather have one of our specialists provide an accurate answer instead of giving you incomplete information.



With your permission, I'll notify our team and they'll get back to you."



The backend then performs the escalation.



\---



\# 34. Budget Questions



Important Rule



The assistant must NEVER invent pricing.



Never estimate.



Never guess.



Never compare with competitors.



If official pricing exists inside the knowledge base,



use it.



Otherwise,



trigger escalation.



\---



\# 35. Human Requests



If the user says:



"I want to talk to someone."



"I want support."



"I want a callback."



"I want your sales team."



Immediately request backend escalation.



Do not attempt to avoid the request.



\---



\# 36. Conversation Completion



A conversation ends when:



\* user leaves

\* meeting booked

\* escalation complete

\* lead collected

\* user explicitly ends conversation



Before closing,



generate:



\* conversation summary

\* structured lead object

\* final lead score (backend)

\* data completeness

\* conversation transcript

\* Google Sheets update

\* PostgreSQL update

---



\# 37. Backend Philosophy



FastAPI is the heart of the application.



The LLM is only a service used by FastAPI.



Every business decision must originate from deterministic backend logic.



The backend owns:



\* Application State

\* Authentication

\* Database

\* Lead Score

\* Meeting Engine

\* Email

\* Google Sheets

\* PostgreSQL

\* Conversation State

\* Logging

\* Tool Execution



The LLM owns only conversation.



\---



\# 38. Clean Architecture



Use layered architecture.



```text

Frontend



↓



API Layer



↓



Service Layer



↓



Business Logic



↓



Repository Layer



↓



Database

```



Never place business logic inside API routes.



Never place SQL queries inside routers.



Never place Google Sheets logic inside routers.



Keep responsibilities separated.



\---



\# 39. Suggested Project Structure



```text

app/



routers/



services/



repositories/



models/



schemas/



database/



conversation/



meeting/



lead\_scoring/



google\_sheets/



email/



rag/



speech/



tts/



stt/



auth/



dashboard/



config/



utils/



tests/

```



\---



\# 40. API Design



Keep APIs RESTful where possible.



Example routes



```text

POST /conversation/start



POST /conversation/message



POST /conversation/end



POST /meeting/book



POST /lead/update



POST /admin/login



GET /admin/conversations



GET /admin/conversation/{id}



GET /admin/meetings

```



Do not create massive APIs.



Each endpoint should have one responsibility.



\---



\# 41. WebSockets



Use WebSockets for the live voice session.



Reason:



Real-time communication.



The browser should maintain one persistent connection during the conversation.



Avoid repeated HTTP requests for streaming audio.



\---



\# 42. Voice Session Lifecycle



Example



```text

User Opens Page



↓



Create Conversation ID



↓



Open WebSocket



↓



Microphone Starts



↓



Streaming Audio



↓



Streaming STT



↓



Streaming LLM



↓



Streaming TTS



↓



Conversation Ends



↓



Persist Data



↓



Close WebSocket

```



\---



\# 43. Conversation ID



Generate a UUID.



Example



```text

conversation\_id



550e8400...

```



Store this throughout the conversation.



Everything references this ID.



\---



\# 44. Browser Session



Store Conversation ID locally.



Do NOT require login.



Anonymous visitors should still be able to talk.



When contact details are collected,



associate them with the conversation.



\---



\# 45. Speech-To-Text



Use:



faster-whisper



Small model



during development.



The implementation should allow future replacement with:



\* Medium

\* Large

\* API providers



without changing application logic.



\---



\# 46. STT Responsibilities



Speech-To-Text should only:



Convert audio



↓



Text



Nothing else.



No business logic.



No prompt logic.



No extraction.



\---



\# 47. LLM Integration



Initial provider



Groq



The provider must be abstracted.



Create an interface.



Example



```python

class LLMProvider:



&#x20;   async def generate():

&#x20;       ...

```



Future providers



\* OpenRouter

\* Gemini

\* Local Qwen

\* Local Gemma

\* Local Llama



should require minimal code changes.



\---



\# 48. System Prompt



The system prompt should NOT contain company knowledge.



Company knowledge belongs inside RAG.



The system prompt should contain only:



\* Behaviour

\* Personality

\* Rules

\* Tool usage

\* Conversation guidelines



\---



\# 49. LLM Responsibilities



The LLM should:



Answer naturally



Ask follow-up questions



Use retrieved context



Extract structured information



Request backend tools



Nothing more.



\---



\# 50. Structured Outputs



The LLM should never return free-form business data.



Instead return structured JSON.



Example



```json

{

&#x20; "assistant\_message": "...",



&#x20; "updated\_fields": {

&#x20;   "business": "Dental Clinic",

&#x20;   "timeline": "2 Months"

&#x20; },



&#x20; "tool\_calls": \[]

}

```



The backend updates the lead object.



\---



\# 51. Tool Calling



The LLM never performs actions.



Instead it requests actions.



Example



```json

{

&#x20; "tool": "schedule\_meeting"

}

```



or



```json

{

&#x20; "tool": "escalate\_to\_human"

}

```



FastAPI executes them.



\---



\# 52. Supported Tools



Initially implement:



update\_lead



calculate\_score



schedule\_meeting



escalate\_to\_human



save\_conversation



generate\_summary



send\_email



append\_google\_sheet



retrieve\_rag



The Conversation Manager decides when to invoke them.



\---



\# 53. Incremental Lead Object



Maintain a structured object.



Example



```json

{

&#x20; "name": null,



&#x20; "phone": null,



&#x20; "business": "Dental Clinic",



&#x20; "industry": "Healthcare",



&#x20; "budget": null,



&#x20; "timeline": "2 Months",



&#x20; "decision\_maker": true

}

```



Every update modifies only the changed fields.



\---



\# 54. Conversation State



Maintain state separately.



Example



```text

Greeting



Discovery



Qualification



Meeting



Completed

```



Conversation state is backend state.



Never let the LLM manage application flow.



\---



\# 55. Text-To-Speech



Initial model



Kokoro



Wrap it behind an interface.



Example



```python

class SpeechProvider:



&#x20;   async def speak():

&#x20;       ...

```



Future providers should be replaceable.



\---



\# 56. TTS Behaviour



Speech should:



Start quickly



Stop immediately when interrupted



Resume naturally



Support streaming if possible



\---



\# 57. Interruptions



When user starts speaking



Immediately



Stop TTS



Cancel remaining speech



Resume STT



Resume conversation



This behaviour is mandatory.



\---



\# 58. Conversation Transcript



Every interaction must be stored.



Example



```text

Timestamp



Speaker



Message



Latency



Tool Calls

```



Never rely on summaries alone.



Keep the complete transcript.



\---



\# 59. Latency Logging



Log every stage.



Example



```text

STT Time



RAG Time



LLM Time



TTS Time



Total Time

```



These logs are invaluable for optimisation.



\---



\# 60. Error Handling



Every external dependency must fail gracefully.



Examples



Whisper unavailable



↓



Notify user politely



Groq unavailable



↓



Retry



↓



Fallback message



Google Sheets unavailable



↓



Queue update



↓



Retry later



Never crash the conversation.



\---



\# 61. Retry Strategy



Transient failures should retry automatically.



Do not retry indefinitely.



Log failures.



Notify administrators if persistent.



\---



\# 62. Configuration



Never hardcode:



API Keys



Passwords



Database URLs



Email Credentials



Collection Names



Environment



Everything should come from environment variables.



\---



\# 63. Dependency Injection



Services should be injected.



Avoid global state.



This improves testing.



\---



\# 64. Unit Testing



Business logic should be independently testable.



Especially:



Lead Score



Meeting Engine



Conversation Manager



Escalation Rules



Data Completeness



These should not require an LLM to test.



\---



\# 65. RAG Philosophy



The AI must never answer company-specific questions from its own pretrained knowledge.



Every company-related answer must originate from the company's Knowledge Base.



The LLM should behave as though it knows nothing about PP5 Media Solutions until relevant context is retrieved.



If no relevant context is found, the assistant should admit it does not have enough information and, when appropriate, offer to escalate to a human.



Never hallucinate.



Never invent.



Never assume.



\---



\# 66. Source of Truth



The Knowledge Base is the single source of truth.



Company knowledge must never be duplicated across:



\* System Prompt

\* Backend Code

\* Hardcoded Python Files

\* Frontend

\* LLM Prompt



The only source of company knowledge is the Markdown Knowledge Base.



\---



\# 67. Knowledge Base Structure



The project will receive Markdown files such as:



```text

knowledge-base/



about-company.md



services.md



pricing.md



faq.md



portfolio.md



case-studies.md



process.md



contact.md

```



Additional Markdown files may be added in the future without requiring backend code changes.



\---



\# 68. Indexing Pipeline



The indexing pipeline should follow:



```text

Markdown Files



↓



Document Loader



↓



Cleaning



↓



Chunking



↓



Embedding



↓



Qdrant Collection

```



The indexing pipeline should be independent of the application.



Re-indexing should not require modifying backend code.



\---



\# 69. Chunking Strategy



Do not embed an entire document as one vector.



Instead:



Split documents into meaningful semantic chunks.



Avoid chunks that are:



\* Too short

\* Too large

\* Unrelated



Prefer overlapping chunks so context is preserved.



\---



\# 70. Metadata



Every chunk should contain metadata.



Example:



```json

{

&#x20; "source": "pricing.md",



&#x20; "section": "Website Packages",



&#x20; "chunk\_id": "...",



&#x20; "last\_updated": "...",



&#x20; "title": "Website Development"

}

```



Metadata improves debugging and future filtering.



\---



\# 71. Embedding Layer



The embedding implementation should be abstracted.



Do not tightly couple the application to one provider.



Create an Embedding Service.



Future models should be replaceable without changing application logic.



\---



\# 72. Qdrant Collection



Create a dedicated collection for the Voice Agent.



Do not reuse the WhatsApp chatbot's runtime collection.



Each project should own its own vector index.



Both projects may share the same Markdown files.



\---



\# 73. Retrieval Pipeline



Every user question follows:



```text

User Question



↓



Embedding



↓



Vector Search



↓



Top Results



↓



Context Assembly



↓



LLM

```



The LLM should never receive the entire knowledge base.



Only the retrieved context.



\---



\# 74. Retrieval Rules



Retrieve only relevant context.



Avoid unnecessary chunks.



Avoid duplicate chunks.



If nothing relevant is found,



return no context rather than unrelated context.



\---



\# 75. Context Assembly



Before sending context to the LLM:



Remove duplicates.



Maintain logical ordering.



Preserve document structure where possible.



The context should read naturally.



\---



\# 76. Prompt Construction



Every LLM request should contain:



System Prompt



\*



Conversation History



\*



Retrieved Context



\*



Current Lead Object



\*



Conversation State



The LLM should have everything required to continue naturally.



\---



\# 77. System Prompt Rules



The System Prompt should define:



Identity



Behaviour



Conversation Rules



Tool Calling Rules



Escalation Rules



Safety Rules



It should NOT contain:



Company services



Pricing



FAQs



Portfolio



Case studies



Those belong to RAG.



\---



\# 78. Conversation History



Send only the required history.



Do not send the full transcript if it becomes excessively long.



Implement a rolling context strategy.



Older information should be summarized while preserving important facts.



The backend should manage this, not the LLM.



\---



\# 79. Retrieved Context Priority



When retrieved context exists,



it overrides the LLM's pretrained knowledge.



If retrieved context contradicts prior knowledge,



the retrieved context wins.



\---



\# 80. Unknown Information



If the knowledge base does not contain the answer,



the assistant should respond naturally.



Example behaviour:



"I don't currently have enough information to answer that accurately.



Rather than guessing, I can notify our team so they can get back to you."



Never fabricate an answer.



\---



\# 81. Pricing Rules



Pricing is sensitive.



If pricing exists in the knowledge base,



use only the documented pricing.



If custom pricing is required,



do not estimate.



Trigger escalation.



\---



\# 82. Company Policies



If a policy exists,



quote or summarize only what exists.



Never create new policies.



Never infer company policies.



\---



\# 83. Portfolio Questions



Answer only using documented portfolio items.



Never invent projects.



Never exaggerate experience.



\---



\# 84. Case Studies



Use documented case studies only.



Do not create fictional customer stories.



\---



\# 85. Hallucination Prevention



Before responding,



the assistant should internally follow this order:



1\. Search Knowledge Base.



2\. Determine whether enough information exists.



3\. If yes, answer.



4\. If partially available, answer only the supported portion.



5\. If unavailable, escalate or acknowledge uncertainty.



Never fill missing information with guesses.



\---



\# 86. Retrieval Failures



If Qdrant is temporarily unavailable:



Do not crash the conversation.



Respond politely.



Log the failure.



Offer escalation if necessary.



The application should remain usable.



\---



\# 87. Knowledge Base Updates



When Markdown files change,



developers should only need to:



Run the indexing pipeline.



The Voice Agent should immediately use the updated knowledge.



No prompt modifications should be required.



\---



\# 88. Future Expansion



The architecture should allow adding:



\* PDFs

\* DOCX

\* Company policies

\* Contracts

\* Internal documentation

\* Brochures



without changing the conversation engine.



Only the indexing pipeline should evolve.



\---



\# 89. Logging Retrieval



For debugging,



log:



\* User Question

\* Retrieved Documents

\* Similarity Scores

\* Chosen Context

\* LLM Response



This makes retrieval quality measurable.



\---



\# 90. Knowledge Separation



Company knowledge belongs only inside RAG.



Business rules belong only inside FastAPI.



Conversation behaviour belongs only inside the System Prompt.



This separation must always be maintained.



\---



\# 91. Final Principle



The objective is not to build a chatbot that "knows everything."



The objective is to build a consultant that:



\* knows when to search,

\* knows when to answer,

\* knows when to ask another question,

\* and knows when to say "I don't know."



That behaviour builds trust and prevents hallucinations.



\---

\# 92. Database Philosophy



PostgreSQL is the operational database for this project.



It is responsible for storing:



\* Conversation history

\* Lead object

\* Meeting schedule

\* Authentication

\* Conversation metadata

\* AI summaries

\* Tool execution history

\* Conversation analytics



Google Sheets is \*\*not\*\* the primary database.



Google Sheets is only:



\* Lead log

\* Email workflow

\* Quick business reference



PostgreSQL is the source of truth.



\---



\# 93. Database Design Principles



Normalize where appropriate.



Avoid duplicate data.



Use foreign keys.



Use indexes.



Never store business logic inside SQL.



Business logic belongs in FastAPI.



\---



\# 94. Main Tables



Create at minimum:



```text

admins



conversations



messages



leads



meetings



tool\_calls



conversation\_summaries

```



The schema should allow future expansion without redesign.



\---



\# 95. Conversations Table



Each conversation represents one browser session.



Suggested fields:



```text

conversation\_id



started\_at



ended\_at



status



lead\_score



lead\_status



data\_completeness



summary\_id



meeting\_id



lead\_id



escalated



escalation\_reason



last\_activity

```



\---



\# 96. Messages Table



Store every message.



Suggested fields:



```text

message\_id



conversation\_id



speaker



message



timestamp



latency



message\_type

```



Speaker:



\* User

\* Assistant

\* System



Nothing should ever overwrite previous messages.



Keep the complete transcript.



\---



\# 97. Leads Table



The lead object should exist independently.



Suggested fields:



```text

lead\_id



conversation\_id



name



phone



email



business



industry



requirement



monthly\_leads



company\_size



budget



timeline



decision\_maker



lead\_score



lead\_status



data\_completeness



escalated



escalation\_reason

```



FastAPI updates this table incrementally throughout the conversation.



\---



\# 98. Meetings Table



Suggested fields:



```text

meeting\_id



conversation\_id



date



time



status



notes



created\_at



updated\_at

```



Status examples:



\* Available

\* Reserved

\* Confirmed

\* Cancelled

\* Completed



\---



\# 99. Conversation Summary Table



The summary should be separate.



Suggested fields:



```text

summary\_id



conversation\_id



summary



generated\_at

```



The summary should be AI-generated after the conversation ends.



The summary should be concise and business-focused.



\---



\# 100. Tool Call Table



Store every backend tool invocation.



Suggested fields:



```text

tool\_call\_id



conversation\_id



tool\_name



input



output



status



timestamp

```



This will help debug conversations.



\---



\# 101. Authentication



Create a dedicated authentication module.



Only administrators require authentication.



Visitors should never need an account.



\---



\# 102. Admin Accounts



Store only:



\* username

\* password\_hash

\* role



Never store plaintext passwords.



Use bcrypt or Argon2.



\---



\# 103. Authentication Flow



```text

Admin Login



↓



Validate Credentials



↓



Generate JWT



↓



Store Secure Cookie or Token



↓



Access Dashboard

```



Expired sessions should require re-authentication.



\---



\# 104. Dashboard Route



Create:



```text

/voice-agent/admin

```



This route must always require authentication.



Unauthenticated users should never access internal data.



\---



\# 105. Dashboard Philosophy



This is \*\*not\*\* a CRM.



This is \*\*not\*\* an analytics platform.



It is an operational dashboard for viewing conversations and meetings.



Keep it simple.



Keep it fast.



Keep it clean.



\---



\# 106. Dashboard Layout



Suggested navigation:



```text

Dashboard



├── Conversations



├── Meetings



└── Logout

```



Do not overload the interface.



\---



\# 107. Conversations Screen



Display a list of conversations.



Each row may include:



```text

Name



Business



Lead Score



Lead Status



Meeting Status



Started At



Last Activity

```



Support pagination.



Support search.



Support sorting.



\---



\# 108. Conversation Details



Clicking a conversation opens:



General Information



Lead Information



Conversation Summary



Full Transcript



Meeting Information



Tool Call History



Everything should be available on one page.



\---



\# 109. Transcript Viewer



Display messages in chronological order.



Example:



```text

10:01



User



I need a website.



\---------------------



10:02



Assistant



Certainly.

May I ask what kind of business you operate?



\---------------------



10:03



User



Dental Clinic

```



Preserve timestamps.



Do not edit stored messages.



\---



\# 110. Meeting Screen



Display all meetings.



Columns:



```text

Name



Business



Date



Time



Status

```



Support:



\* Search

\* Sort

\* Filter



\---



\# 111. Meeting Booking Philosophy



Do NOT integrate Google Calendar initially.



The meeting system belongs entirely to this project.



The backend owns scheduling.



\---



\# 112. Available Slots



Maintain available slots inside PostgreSQL.



Example:



```text

Monday



10 AM



11 AM



2 PM



4 PM

```



The assistant retrieves these from FastAPI.



\---



\# 113. Booking Logic



Flow:



```text

User Requests Meeting



↓



Conversation Manager



↓



Meeting Engine



↓



Available Slots



↓



Assistant Presents Options



↓



User Chooses



↓



Reserve Slot



↓



Store Database



↓



Update Google Sheets



↓



Send Confirmation Email

```



The assistant should never invent available times.



\---



\# 114. Double Booking Prevention



Before confirming:



Always verify that the slot is still available.



Use transactions where appropriate.



Never allow two conversations to reserve the same slot.



\---



\# 115. Future Expandability



Design the Meeting Engine so it can later integrate with:



\* Google Calendar

\* Outlook Calendar

\* Internal Company Calendar



without changing conversation logic.



The Meeting Engine should expose a clean interface.



\---



\# 116. Conversation Search



The dashboard should support searching conversations by:



\* Name

\* Phone

\* Email

\* Business

\* Conversation ID



Do not search only summaries.



\---



\# 117. Performance



Do not load entire transcripts on the conversations list.



Load transcripts only when a conversation is opened.



Use pagination.



Optimize queries.



\---



\# 118. Security



Never expose:



Database credentials



API keys



JWT secrets



Environment variables



Sensitive logs



Use proper authorization on every admin endpoint.



\---



\# 119. Auditability



Every important backend action should be traceable.



Examples:



Meeting booked



Lead updated



Summary generated



Google Sheet updated



Escalation triggered



Email sent



This makes debugging significantly easier.



\---



\# 120. Final Principle



The admin dashboard should answer one question quickly:



"What happened during this conversation?"



Without opening logs.



Without reading code.



Without checking databases manually.



Everything required to understand the interaction should be available from a single authenticated interface.



\---



\# 121. Business Logic Philosophy



The backend is the decision-maker.



The LLM is never allowed to make business decisions.



The backend is responsible for:



\* Lead Score

\* Lead Status

\* Data Completeness

\* Escalation

\* Email

\* Google Sheets

\* Meeting Reservation

\* Lead Updates



The LLM only requests actions.



FastAPI decides whether they should happen.



\---



\# 122. Lead Object



Maintain one structured lead object during the conversation.



Example



```json

{

&#x20; "conversation\_id": "...",

&#x20; "name": null,

&#x20; "phone": null,

&#x20; "email": null,

&#x20; "business": null,

&#x20; "industry": null,

&#x20; "requirement": null,

&#x20; "monthly\_leads": null,

&#x20; "company\_size": null,

&#x20; "budget": null,

&#x20; "timeline": null,

&#x20; "decision\_maker": null,

&#x20; "lead\_score": 0,

&#x20; "lead\_status": "Cold",

&#x20; "data\_completeness": 0,

&#x20; "meeting\_status": "Not Scheduled",

&#x20; "escalated": false,

&#x20; "escalation\_reason": null

}

```



This object is updated throughout the conversation.



Never recreate it.



Never parse the transcript repeatedly.



\---



\# 123. Incremental Updates



Every time the LLM extracts structured information:



Backend updates only those fields.



Example



User:



"I own a dental clinic."



Backend updates only:



```text

business



industry

```



Everything else remains unchanged.



\---



\# 124. Google Sheets



Create a dedicated Google Sheet for the Voice Agent.



Do NOT reuse the WhatsApp chatbot sheet.



The Voice Agent is an independent project.



\---



\# 125. Google Sheet Columns



Suggested columns:



```text

Conversation ID



Phone



Name



Business



Industry



Requirement



Monthly Leads



Company Size



Budget



Timeline



Decision Maker



Lead Score



Lead Status



Data Completeness



Conversation Stage



Missing Information



Summary



Meeting Status



Meeting Date



Meeting Time



Escalated



Escalation Reason



Last Updated

```



The backend is responsible for updating these fields.



\---



\# 126. Lead Scoring Philosophy



The lead score must be deterministic.



The same lead must always produce the same score.



Never use the LLM to calculate scores.



Never estimate.



Never infer.



\---



\# 127. Lead Score Calculation



Maximum Score = 100



\## Strong Buying Intent



25 Points



Award if ANY of the following occur:



\* User explicitly requests a meeting.

\* User requests a callback.

\* User asks to speak with the team.

\* Backend triggers escalation.

\* User requests a quotation.

\* User requests custom pricing.



Otherwise



0 Points.



\---



\## Monthly Leads



10 Points



Award only if the user provides monthly lead information.



Otherwise



0\.



\---



\## Company Size



5 Points



Award only if company size is known.



Otherwise



0\.



\---



\## Decision Maker



10 Points



Award only if the user confirms they are the decision maker.



Otherwise



0\.



\---



\## Timeline



10 Points



Award only if the project timeline is known.



Otherwise



0\.



\---



\## Budget



10 Points



Award only if the user voluntarily provides a budget or budget range.



Otherwise



0\.



\---



\## Requirement



15 Points



Award only if the project requirement is clearly understood.



Otherwise



0\.



\---



\## Business / Industry



15 Points



Award only if both business and industry are identified.



Otherwise



0\.



\---



\# 128. Lead Categories



```text

Score >= 70



Hot Lead



\------------------



40 <= Score < 70



Warm Lead



\------------------



Score < 40



Cold Lead

```



Always recalculate after every lead update.



\---



\# 129. Data Completeness



Lead Score measures buying intent.



Data Completeness measures information collected.



These are different metrics.



\---



\# 130. Completeness Fields



Track:



Name



Phone



Email



Business



Industry



Requirement



Monthly Leads



Company Size



Budget



Timeline



Decision Maker



Meeting Status



Each completed field increases completeness.



\---



\# 131. Missing Information



Maintain a list.



Example



```text

Budget



Timeline



Phone Number

```



The Conversation Manager uses this list to determine the next follow-up question.



\---



\# 132. Escalation Philosophy



Escalation is a backend event.



The LLM may request escalation.



FastAPI decides whether to execute it.



\---



\# 133. Escalation Rules



Escalate if:



\* User requests a human.

\* User requests support.

\* User requests a callback.

\* User requests custom pricing.

\* User requests a quotation.

\* AI cannot confidently answer.

\* Backend determines escalation is required.



\---



\# 134. Escalation Reason



Always record the reason.



Possible values:



```text

Human Requested



Quotation



Budget



Pricing



Technical Question



Custom Requirement



Unknown Information



Low Confidence



Other

```



Never leave escalation without a reason.



\---



\# 135. Email Notifications



Emails are backend generated.



Never ask the LLM to generate operational emails.



\---



\# 136. Email Trigger Events



Send email when:



New Lead Completed



Meeting Scheduled



Escalation Triggered



Meeting Cancelled



Optional future events can be added later.



\---



\# 137. Lead Email



The lead email should contain:



Conversation ID



Name



Phone



Email



Business



Requirement



Lead Score



Lead Status



Meeting Status



Summary



Escalation Status



Conversation Link



Timestamp



Keep it concise.



\---



\# 138. Conversation Summary



The LLM should generate a short business summary.



Example



```text

Client owns a dental clinic.



Looking for a business website.



Timeline is two months.



Decision maker confirmed.



Meeting scheduled for Friday 2 PM.

```



The summary should be operational, not conversational.



\---



\# 139. Conversation URL



Every conversation should have a dashboard URL.



Example



```text

/voice-agent/admin/conversations/{conversation\_id}

```



Store this in the email.



This allows staff to immediately review the conversation.



\---



\# 140. Google Sheets Synchronization



Google Sheets is updated only by FastAPI.



Never by the frontend.



Never by the LLM.



The backend owns synchronization.



\---



\# 141. Backend Validation



Before writing data:



Validate:



Phone Number



Email



Date



Time



Lead Score



Status



Required fields



Reject invalid data.



\---



\# 142. Idempotency



Running the same update twice should not create duplicate rows.



Updates should modify existing records.



Not insert duplicates.



\---



\# 143. Logging



Every backend decision should be logged.



Example:



Lead score recalculated



↓



82



↓



Hot Lead



Meeting booked



↓



Friday 2 PM



Escalation



↓



Budget Request



This greatly simplifies debugging.



\---



\# 144. Final Principle



Business logic must remain deterministic forever.



If company rules change,



developers should update backend code,



not prompts.



The AI should remain focused on conversation,



while FastAPI remains responsible for every business operation.



\---



\# 145. Development Strategy



This project should be developed incrementally.



Never attempt to build the complete application in a single iteration.



Each milestone must:



\* Compile successfully

\* Run successfully

\* Be manually tested

\* Be committed before moving forward



No new milestone should begin until the previous one is stable.



\---



\# 146. Local Development



The primary development environment is the local machine.



Everything should run locally.



Current expected stack:



```text

Existing Website



↓



Voice Agent Page



↓



FastAPI



↓



Docker Compose



↓



PostgreSQL



↓



Qdrant



↓



Whisper



↓



Kokoro



↓



Groq API

```



Do not optimize for cloud deployment yet.



Correctness is more important than deployment.



\---



\# 147. Docker Philosophy



Every service should have one responsibility.



Example services:



```text

frontend



backend



postgres



qdrant



(optional) whisper



(optional) kokoro

```



Avoid giant monolithic containers.



\---



\# 148. Environment Variables



Never hardcode:



\* API Keys

\* Email Credentials

\* JWT Secret

\* PostgreSQL URL

\* Google Sheets Credentials

\* Groq API Key

\* SMTP Credentials

\* Collection Names



Everything must come from:



```text

.env

```



Provide:



```

.env.example

```



containing every required variable.



\---



\# 149. Configuration Layer



Create a centralized configuration module.



Never scatter environment variable reads across the project.



Example:



```python

config.settings.database\_url



config.settings.jwt\_secret



config.settings.groq\_api\_key

```



\---



\# 150. Logging



Implement structured logging.



Every important event should be logged.



Examples:



Conversation Started



Conversation Ended



Meeting Booked



Lead Updated



Lead Score Changed



Google Sheets Updated



Email Sent



Escalation Triggered



Tool Executed



Database Error



RAG Retrieval



LLM Error



STT Error



TTS Error



\---



\# 151. Error Handling



Every external dependency must fail gracefully.



Examples:



Groq unavailable



↓



Retry



↓



Graceful message



↓



Continue if possible



PostgreSQL unavailable



↓



Log



↓



Return meaningful error



Whisper unavailable



↓



Notify user politely



↓



Do not crash



The application should never terminate because one dependency failed.



\---



\# 152. Testing Philosophy



Every important backend module must be independently testable.



Especially:



Lead Score Engine



Meeting Engine



Conversation Manager



Escalation Engine



Google Sheets Service



Email Service



Authentication



Repository Layer



Testing should not require the LLM.



Testing should not require speech models.



\---



\# 153. Code Quality



Every function should have one responsibility.



Avoid:



\* Long functions

\* Duplicate logic

\* Hidden side effects



Prefer:



Small modules.



Readable code.



Clear naming.



Maintainability over cleverness.



\---



\# 154. Naming Conventions



Use descriptive names.



Good:



```text

calculate\_lead\_score()



update\_google\_sheet()



schedule\_meeting()



generate\_summary()

```



Avoid vague names.



\---



\# 155. Type Safety



Use Python type hints everywhere.



Define Pydantic models for:



Requests



Responses



Database Models



Tool Calls



Lead Object



Meeting Object



Conversation State



Avoid raw dictionaries where structured models are appropriate.



\---



\# 156. Documentation



Every major module should contain documentation.



Especially:



Conversation Manager



Meeting Engine



Lead Score Engine



RAG Pipeline



Authentication



Admin Dashboard



The next developer should understand the architecture without reading every file.



\---



\# 157. Git Workflow



Commit after every completed milestone.



Suggested commit style:



```

feat: implement conversation manager



feat: add meeting engine



feat: integrate whisper



fix: improve interruption handling



refactor: split lead scoring module

```



Keep commits focused.



\---



\# 158. Future Deployment



The application should be designed so local development can later be migrated to a VPS with minimal changes.



Migration should only require:



Environment variable updates



Docker deployment



Domain configuration



Reverse proxy



SSL



No architectural redesign.



\---



\# 159. Performance Goals



Target user experience:



Conversation start should feel immediate.



Speech recognition should feel responsive.



AI responses should begin quickly.



Speech playback should begin quickly.



Interruptions should stop speech immediately.



Perceived latency is more important than benchmark latency.



\---



\# 160. Security



Never expose:



API Keys



JWT Secrets



Database Passwords



SMTP Credentials



Google Credentials



Admin Routes



Protect every admin endpoint.



Validate every request.



Sanitize every input.



\---



\# 161. AI IDE Behaviour



Before implementing any feature:



Understand existing code.



Explain intended architecture.



Identify affected modules.



Implement only the requested functionality.



Avoid unrelated refactoring.



When uncertain,



ask for clarification instead of making assumptions.



\---



\# 162. Features Explicitly Out of Scope (Current Version)



Do NOT implement unless requested later:



\* Multi-language UI

\* CRM

\* Billing

\* Payment Gateway

\* Google Calendar Integration

\* Outlook Integration

\* User Accounts

\* Client Portal

\* Team Management

\* Analytics Dashboard

\* Usage Analytics

\* Multiple Companies

\* Multiple Tenants



Keep Version 1 focused.



\---



\# 163. Project Milestones



\## Milestone 1



Project setup



Folder structure



Docker Compose



Configuration



Database



\---



\## Milestone 2



Voice page



WebSocket



Microphone



Streaming



\---



\## Milestone 3



Whisper integration



Streaming transcription



Interruptions



\---



\## Milestone 4



Groq integration



Conversation Manager



Structured outputs



Tool calling



\---



\## Milestone 5



Qdrant



Knowledge Base



Retrieval



Hallucination prevention



\---



\## Milestone 6



Lead Object



Lead Scoring



Data Completeness



Escalation



Google Sheets



Email



\---



\## Milestone 7



Meeting Engine



Meeting Booking



Confirmation Flow



\---



\## Milestone 8



PostgreSQL



Conversation History



Transcript Storage



Admin Authentication



\---



\## Milestone 9



Admin Dashboard



Conversation Viewer



Meeting Viewer



Search



\---



\## Milestone 10



End-to-end testing



Bug fixing



Performance optimization



Documentation



\---



\# 164. Definition of Success



The project is successful when a visitor can:



\* Visit the website.

\* Open the Voice Agent.

\* Speak naturally.

\* Interrupt naturally.

\* Receive accurate company information.

\* Be asked intelligent follow-up questions.

\* Have their lead information collected.

\* Receive a meeting invitation.

\* Book a meeting.

\* Trigger escalation when appropriate.

\* Have the conversation stored.

\* Have the lead stored.

\* Have the company notified.



All without human intervention unless escalation is required.



\---



\# 165. Non-Negotiable Engineering Rules



These rules must never be violated.



1\. The LLM is never the source of truth.



2\. FastAPI owns all business logic.



3\. PostgreSQL is the operational database.



4\. Google Sheets is a lead log and notification integration.



5\. Company knowledge belongs only in the Knowledge Base.



6\. Business rules belong only in the backend.



7\. Conversation behaviour belongs only in the System Prompt.



8\. Every feature must be modular.



9\. Every feature must be testable.



10\. Every feature should be replaceable without rewriting the application.



\---



\# 166. Final Objective



Build a Voice Agent that feels like speaking to a knowledgeable consultant, not a chatbot.



The system should be:



\* Natural

\* Reliable

\* Deterministic

\* Modular

\* Maintainable

\* Production-ready

\* Easy to extend



Every architectural decision should move the project closer to becoming a long-term product rather than a short-term demonstration.



\---



This document is the authoritative specification for the project.



When implementing features, always follow this document unless explicit new requirements are provided by the developer.









