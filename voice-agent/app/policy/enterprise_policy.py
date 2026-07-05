"""
Enterprise Policy — Input and output validation for security and
business correctness.

Validates both:
  1. Syntax safety: No XML, function tags, JSON payloads, internal IDs
  2. Business correctness: No invented pricing, unsupported claims,
     internal exposure, or over-promising
"""
import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Result of output validation."""
    is_valid: bool
    sanitized_response: str
    violations: list[str] = field(default_factory=list)
    was_modified: bool = False


# ── Compiled patterns for output validation ───────────────────────────────

# Syntax leakage patterns
_XML_TAGS = re.compile(r"</?(?:function|tool_call|system|assistant|user|tool)[^>]*>", re.IGNORECASE)
_FUNCTION_SYNTAX = re.compile(r"<function=[^>]+>[^<]*(?:</function>)?", re.IGNORECASE)
_JSON_PAYLOADS = re.compile(r"\{\"(?:tool_call_id|function|name|arguments|role|content)\":\s*\"[^\"]*\"[^}]*\}")
_TOOL_SCHEMA = re.compile(r"\{\"type\":\s*\"function\".*?\"parameters\".*?\}", re.DOTALL)

# Internal exposure patterns
_INTERNAL_IDS = re.compile(
    r"\b(?:lead_id|conversation_id|meeting_id|user_id|session_id)\s*[=:]\s*\d+",
    re.IGNORECASE,
)
_INTERNAL_TECH = re.compile(
    r"\b(?:Qdrant|Groq|FastAPI|SQLAlchemy|uvicorn|websocket\.send|"
    r"AsyncSession|GROQ_API_KEY|\.env|api_key|model_used|"
    r"llama[\s-]?3|system prompt|tool_definitions|PolicyEngine|"
    r"ConversationManager|LeadStateManager|rag_retriever)\b",
    re.IGNORECASE,
)
_PROMPT_FRAGMENTS = re.compile(
    r"(?:YOUR CORE OBJECTIVES|TOOL EXECUTION|LEAD COLLECTION STRATEGY|"
    r"IDENTITY & CONSTRAINTS|CONVERSATION STYLE|SYSTEM:|"
    r"--- START CONTEXT ---|--- END CONTEXT ---)",
    re.IGNORECASE,
)

# Business correctness patterns
_INVENTED_PRICING = re.compile(
    r"\$\s?\d[\d,]*(?:\.\d{2})?\s*(?:per|/|a)\s*(?:month|year|hour|project|page|website)",
    re.IGNORECASE,
)
_GUARANTEE_CLAIMS = re.compile(
    r"\b(?:guarantee|guaranteed|100%|promise|ensure|certain|definitely will|"
    r"absolutely will|we always deliver|never fail)\b",
    re.IGNORECASE,
)
_COMPETITOR_DISPARAGEMENT = re.compile(
    r"\b(?:better than|worse than|unlike|compared to)\s+(?:Wix|WordPress|Squarespace|"
    r"Shopify|GoDaddy|HubSpot|Salesforce)\b",
    re.IGNORECASE,
)

# Safe fallback when entire response is invalid
SAFE_FALLBACK = (
    "I'd love to help you with that. Could you tell me a bit more about "
    "what you're looking for so I can give you the most accurate information?"
)


class EnterprisePolicy:
    """
    Enforces enterprise security and business correctness rules.
    Applied both before (input) and after (output) LLM requests.
    """

    # ── Output Validation ─────────────────────────────────────────────

    def validate_output(
        self,
        response: str,
        rag_was_invoked: bool = False,
    ) -> ValidationResult:
        """
        Validate and sanitize the LLM output.
        Returns a ValidationResult with the sanitized response and
        any violations detected.
        """
        violations = []
        sanitized = response
        was_modified = False

        # ── Pass 1: Syntax safety ─────────────────────────────────────
        sanitized, v = self._strip_syntax_leaks(sanitized)
        violations.extend(v)
        if v:
            was_modified = True

        # ── Pass 2: Internal exposure ─────────────────────────────────
        sanitized, v = self._strip_internal_exposure(sanitized)
        violations.extend(v)
        if v:
            was_modified = True

        # ── Pass 3: Business correctness ──────────────────────────────
        biz_violations = self._check_business_correctness(sanitized, rag_was_invoked)
        violations.extend(biz_violations)
        # Business violations are logged but we don't strip the text —
        # the response may still be usable. Only flag for review.

        # ── Final check: Is there anything left? ──────────────────────
        stripped = sanitized.strip()
        if not stripped or len(stripped) < 5:
            sanitized = SAFE_FALLBACK
            violations.append("EMPTY_RESPONSE: entire response was invalid")
            was_modified = True

        return ValidationResult(
            is_valid=len(violations) == 0,
            sanitized_response=sanitized,
            violations=violations,
            was_modified=was_modified,
        )

    def _strip_syntax_leaks(self, text: str) -> tuple[str, list[str]]:
        """Remove XML tags, function syntax, JSON payloads."""
        violations = []

        if _FUNCTION_SYNTAX.search(text):
            text = _FUNCTION_SYNTAX.sub("", text)
            violations.append("SYNTAX_LEAK: function call syntax detected and stripped")

        if _XML_TAGS.search(text):
            text = _XML_TAGS.sub("", text)
            violations.append("SYNTAX_LEAK: XML tags detected and stripped")

        if _JSON_PAYLOADS.search(text):
            text = _JSON_PAYLOADS.sub("", text)
            violations.append("SYNTAX_LEAK: JSON tool payload detected and stripped")

        if _TOOL_SCHEMA.search(text):
            text = _TOOL_SCHEMA.sub("", text)
            violations.append("SYNTAX_LEAK: tool schema definition detected and stripped")

        return text.strip(), violations

    def _strip_internal_exposure(self, text: str) -> tuple[str, list[str]]:
        """Remove internal IDs, tech stack names, prompt fragments."""
        violations = []

        if _INTERNAL_IDS.search(text):
            text = _INTERNAL_IDS.sub("[REDACTED]", text)
            violations.append("INTERNAL_EXPOSURE: internal IDs detected and redacted")

        if _INTERNAL_TECH.search(text):
            # Don't strip tech names entirely — just flag them
            matches = _INTERNAL_TECH.findall(text)
            violations.append(
                f"INTERNAL_EXPOSURE: internal tech references detected: {', '.join(set(matches))}"
            )

        if _PROMPT_FRAGMENTS.search(text):
            text = _PROMPT_FRAGMENTS.sub("", text)
            violations.append("PROMPT_LEAK: system prompt fragments detected and stripped")

        return text.strip(), violations

    def _check_business_correctness(
        self,
        text: str,
        rag_was_invoked: bool,
    ) -> list[str]:
        """Check for business rule violations (logged, not stripped)."""
        violations = []

        # Flag invented pricing if RAG was not invoked
        if not rag_was_invoked and _INVENTED_PRICING.search(text):
            violations.append(
                "BUSINESS_RISK: specific pricing mentioned without knowledge base context"
            )

        # Flag absolute guarantees
        if _GUARANTEE_CLAIMS.search(text):
            violations.append(
                "BUSINESS_RISK: absolute guarantee or promise language detected"
            )

        # Flag competitor disparagement
        if _COMPETITOR_DISPARAGEMENT.search(text):
            violations.append(
                "BUSINESS_RISK: competitor comparison/disparagement detected"
            )

        return violations

    # ── Input Validation ──────────────────────────────────────────────

    def validate_tool_call(
        self,
        tool_name: str,
        tool_args: dict,
        allowed_tools: list[str],
    ) -> tuple[bool, str]:
        """
        Validate that a tool call is permitted.
        Returns (is_allowed, reason).
        """
        if tool_name not in allowed_tools:
            return False, f"Tool '{tool_name}' is not allowed in the current stage"

        # Specific validation rules
        if tool_name == "extract_lead_info":
            # Don't allow empty extractions
            if not tool_args or all(v is None or v == "" for v in tool_args.values()):
                return False, "extract_lead_info called with no data"

        return True, "OK"
