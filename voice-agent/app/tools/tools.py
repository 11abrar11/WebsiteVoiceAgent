"""
Tool definitions for the Groq LLM tool calling interface.
These tools allow the LLM to check meeting availability and book slots.
"""

# Tool schemas in the OpenAI function-calling format (Groq-compatible)
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_available_meeting_times",
            "description": (
                "Get a list of available meeting time slots for the next few business days. "
                "Call this when the user wants to schedule or book a meeting, or when you want "
                "to offer meeting options to the user."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_meeting",
            "description": (
                "Book a meeting at a specific date and time after the user has confirmed. "
                "Only call this after the user has explicitly agreed to a specific time slot."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "The date for the meeting in ISO format, e.g. '2026-07-01'.",
                    },
                    "time": {
                        "type": "string",
                        "description": "The time for the meeting in 24-hour format, e.g. '10:00'.",
                    },
                },
                "required": ["date", "time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extract_lead_info",
            "description": (
                "Extract structured lead information from the conversation. "
                "Call this silently whenever the user provides new facts about themselves (name, email, phone, company, requirement, budget, timeline, etc.), "
                "OR when they explicitly decline to provide information. "
                "CRITICAL: Continue the conversation naturally. Never mention that you are saving or extracting their info."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "company": {"type": "string"},
                    "industry": {"type": "string"},
                    "requirement": {"type": "string"},
                    "monthly_leads": {"type": "string", "description": "Number of leads they get per month"},
                    "company_size": {"type": "string", "description": "Size or employee count of their company"},
                    "decision_maker": {"type": "string", "enum": ["yes", "no", "unknown"], "description": "Is the user the decision maker? (yes/no)"},
                    "budget": {"type": "string"},
                    "budget_reason": {"type": "string", "description": "If user declined to provide budget, state reason"},
                    "timeline": {"type": "string"},
                    "timeline_reason": {"type": "string", "description": "If user declined, state reason"},
                },
                "required": [],
            },
        },
    },
]
