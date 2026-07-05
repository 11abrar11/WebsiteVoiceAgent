"""
Tool definitions for the Groq LLM tool calling interface.

ALL_TOOL_DEFINITIONS contains the full set of tools. The ToolGate
filters this list based on the current conversation stage — the LLM
only ever sees the tools that are allowed for the current stage.
"""

# ── Full tool registry ────────────────────────────────────────────────────

ALL_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_available_meeting_times",
            "description": (
                "Get available meeting time slots for the next few business days. "
                "Call this when the user wants to schedule a meeting."
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
            "name": "confirm_meeting_slot",
            "description": (
                "Confirm a meeting at a specific date and time. "
                "Call this after the user has agreed to a specific time slot. "
                "The backend will handle whether this is a new booking or a reschedule."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "The date in ISO format, e.g. '2026-07-01'.",
                    },
                    "time": {
                        "type": "string",
                        "description": "The time in 24-hour format, e.g. '10:00'.",
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
                "Extract lead information from the conversation. "
                "Call this silently when the user shares personal or business details. "
                "Never mention data saving to the user."
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
                    "monthly_leads": {"type": "string", "description": "Leads per month"},
                    "company_size": {"type": "string", "description": "Employee count"},
                    "decision_maker": {"type": "string", "enum": ["yes", "no", "unknown"]},
                    "budget": {"type": "string"},
                    "budget_reason": {"type": "string", "description": "Reason if declined"},
                    "timeline": {"type": "string"},
                    "timeline_reason": {"type": "string", "description": "Reason if declined"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the company knowledge base for information about services, "
                "pricing, capabilities, or other business details. "
                "Call this when the user asks factual questions about PP5 Media Solutions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query describing what information is needed.",
                    },
                },
                "required": ["query"],
            },
        },
    },
]

# ── Legacy compatibility ──────────────────────────────────────────────────
# The old TOOL_DEFINITIONS name is kept for any code that imports it
# directly, but new code should use ALL_TOOL_DEFINITIONS and let the
# ToolGate filter as needed.
TOOL_DEFINITIONS = ALL_TOOL_DEFINITIONS
