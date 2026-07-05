"""
Stage Engine — State-driven conversation stage classifier.

Determines the current conversation stage using multiple signals collectively:
  - Current stage (persistence bias)
  - Turn count
  - Lead completeness
  - User message content
  - Previous tool calls in history
  - Active meeting state
  - Chat history patterns

Each stage gets a weighted score. The highest-scoring stage with confidence
above threshold wins. If confidence is too low, falls back to the previous
stage or DISCOVERY.
"""
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Any


class ConversationStage(str, Enum):
    GREETING           = "GREETING"
    DISCOVERY          = "DISCOVERY"
    BUSINESS_DISCOVERY = "BUSINESS_DISCOVERY"
    QUALIFICATION      = "QUALIFICATION"
    KNOWLEDGE          = "KNOWLEDGE"
    MEETING_DISCUSSION = "MEETING_DISCUSSION"
    MEETING_BOOKING    = "MEETING_BOOKING"
    MEETING_RESCHEDULE = "MEETING_RESCHEDULE"
    CLOSING            = "CLOSING"
    UNKNOWN            = "UNKNOWN"


@dataclass
class StageClassification:
    """Result of a stage classification."""
    stage: ConversationStage
    confidence: float              # 0.0 - 1.0
    reason: str                    # Human-readable explanation
    scores: dict = field(default_factory=dict)  # Raw scores for debugging


@dataclass
class StageContext:
    """All signals available to the stage classifier."""
    current_stage: ConversationStage
    turn_count: int
    user_message: str
    chat_history: list[dict]
    lead_known_count: int          # Number of KNOWN fields
    lead_total_fields: int         # Total trackable fields
    lead_declined_fields: list[str]
    has_active_meeting: bool
    active_meeting_info: str | None  # e.g. "July 10 at 2 PM"
    previous_tool_calls: list[str]   # Tool names from history
    rag_was_invoked: bool            # Whether RAG was used in this session


# ── Keyword patterns (compiled once) ──────────────────────────────────────

_KNOWLEDGE_PATTERNS = re.compile(
    r"\b(price|pricing|cost|how much|services?|what do you|offerings?|"
    r"capabilities|features?|portfolio|solutions?|packages?|plans?|"
    r"tell me about|what can you|how does|explain|details?)\b",
    re.IGNORECASE,
)

_MEETING_PATTERNS = re.compile(
    r"\b(meeting|schedule|book|appointment|call|demo|"
    r"available|slot|calendar|set up a|let'?s talk|"
    r"when can|free time|discuss further)\b",
    re.IGNORECASE,
)

_BOOKING_CONFIRM_PATTERNS = re.compile(
    r"\b(yes|confirm|that works|sounds good|perfect|let'?s do|"
    r"book it|go ahead|lock it in|that time|that slot|"
    r"\d{1,2}:\d{2}|\d{1,2}\s?(am|pm)|monday|tuesday|wednesday|"
    r"thursday|friday|tomorrow|next week)\b",
    re.IGNORECASE,
)

_RESCHEDULE_PATTERNS = re.compile(
    r"\b(reschedule|change|move|different time|another time|"
    r"can'?t make it|cancel|postpone|push back|shift)\b",
    re.IGNORECASE,
)

_CLOSING_PATTERNS = re.compile(
    r"\b(goodbye|bye|thanks|thank you|that'?s all|no more|"
    r"done|end|nothing else|have a good|take care|see you|"
    r"that'?s it|i'?m good)\b",
    re.IGNORECASE,
)

_BUSINESS_PATTERNS = re.compile(
    r"\b(my company|we are|our company|employees?|team size|"
    r"industry|sector|business|startup|enterprise|"
    r"founded|revenue|clients?|customers?)\b",
    re.IGNORECASE,
)

# Minimum confidence to accept a stage transition
CONFIDENCE_THRESHOLD = 0.30

# Weight given to the current stage (persistence bias)
STAGE_PERSISTENCE_WEIGHT = 2.0


class StageEngine:
    """
    State-driven conversation stage classifier.
    Uses weighted multi-signal scoring with confidence.
    """

    def classify(self, ctx: StageContext) -> StageClassification:
        """
        Classify the conversation stage based on all available signals.
        Returns the stage, confidence, and reasoning.
        """
        scores: dict[ConversationStage, float] = {stage: 0.0 for stage in ConversationStage}
        reasons: dict[ConversationStage, list[str]] = {stage: [] for stage in ConversationStage}

        # ── Signal 1: Turn count ──────────────────────────────────────
        if ctx.turn_count <= 1:
            scores[ConversationStage.GREETING] += 5.0
            reasons[ConversationStage.GREETING].append("first turn")
        elif ctx.turn_count == 2:
            scores[ConversationStage.GREETING] += 2.0
            reasons[ConversationStage.GREETING].append("second turn")

        # ── Signal 2: Current stage persistence ───────────────────────
        if ctx.current_stage != ConversationStage.UNKNOWN:
            scores[ctx.current_stage] += STAGE_PERSISTENCE_WEIGHT
            reasons[ctx.current_stage].append("stage persistence")

        # ── Signal 3: User message keyword analysis ───────────────────
        msg = ctx.user_message

        if _CLOSING_PATTERNS.search(msg):
            scores[ConversationStage.CLOSING] += 3.5
            reasons[ConversationStage.CLOSING].append("closing keywords detected")

        if _RESCHEDULE_PATTERNS.search(msg) and ctx.has_active_meeting:
            scores[ConversationStage.MEETING_RESCHEDULE] += 4.5
            reasons[ConversationStage.MEETING_RESCHEDULE].append(
                "reschedule keywords + active meeting exists"
            )

        if _BOOKING_CONFIRM_PATTERNS.search(msg) and ctx.current_stage in (
            ConversationStage.MEETING_DISCUSSION,
            ConversationStage.MEETING_BOOKING,
        ):
            scores[ConversationStage.MEETING_BOOKING] += 4.0
            reasons[ConversationStage.MEETING_BOOKING].append(
                "booking confirmation keywords + in meeting flow"
            )

        if _MEETING_PATTERNS.search(msg):
            scores[ConversationStage.MEETING_DISCUSSION] += 4.0
            reasons[ConversationStage.MEETING_DISCUSSION].append("meeting keywords detected")

        if _KNOWLEDGE_PATTERNS.search(msg):
            scores[ConversationStage.KNOWLEDGE] += 3.0
            reasons[ConversationStage.KNOWLEDGE].append("knowledge/service keywords detected")

        if _BUSINESS_PATTERNS.search(msg):
            scores[ConversationStage.BUSINESS_DISCOVERY] += 2.5
            reasons[ConversationStage.BUSINESS_DISCOVERY].append("business info keywords detected")

        # ── Signal 4: Lead completeness ───────────────────────────────
        completeness = ctx.lead_known_count / max(ctx.lead_total_fields, 1)

        if completeness < 0.25:
            scores[ConversationStage.DISCOVERY] += 1.5
            reasons[ConversationStage.DISCOVERY].append(
                f"low lead completeness ({completeness:.0%})"
            )
        elif completeness < 0.55:
            scores[ConversationStage.BUSINESS_DISCOVERY] += 1.0
            reasons[ConversationStage.BUSINESS_DISCOVERY].append(
                f"moderate lead completeness ({completeness:.0%})"
            )
            scores[ConversationStage.QUALIFICATION] += 1.0
            reasons[ConversationStage.QUALIFICATION].append(
                f"moderate lead completeness ({completeness:.0%})"
            )
        else:
            scores[ConversationStage.QUALIFICATION] += 1.5
            reasons[ConversationStage.QUALIFICATION].append(
                f"high lead completeness ({completeness:.0%})"
            )
            # High completeness also makes meeting discussion more likely
            scores[ConversationStage.MEETING_DISCUSSION] += 0.5
            reasons[ConversationStage.MEETING_DISCUSSION].append(
                "lead is well-qualified"
            )

        # ── Signal 5: Previous tool calls ─────────────────────────────
        if "get_available_meeting_times" in ctx.previous_tool_calls:
            scores[ConversationStage.MEETING_BOOKING] += 2.5
            reasons[ConversationStage.MEETING_BOOKING].append(
                "meeting times were already fetched"
            )

        if "search_knowledge_base" in ctx.previous_tool_calls:
            scores[ConversationStage.KNOWLEDGE] += 1.0
            reasons[ConversationStage.KNOWLEDGE].append(
                "knowledge search was already used this session"
            )

        if "confirm_meeting_slot" in ctx.previous_tool_calls:
            # Meeting was already booked — shift toward closing or discovery
            scores[ConversationStage.CLOSING] += 1.5
            reasons[ConversationStage.CLOSING].append(
                "meeting was already confirmed"
            )

        # ── Signal 6: Active meeting state ────────────────────────────
        if ctx.has_active_meeting:
            # Suppress new booking signals
            scores[ConversationStage.MEETING_BOOKING] -= 2.0
            reasons[ConversationStage.MEETING_BOOKING].append(
                "active meeting exists (suppress new booking)"
            )
            # Boost reschedule if meeting keywords present
            if _MEETING_PATTERNS.search(msg):
                scores[ConversationStage.MEETING_RESCHEDULE] += 2.0
                reasons[ConversationStage.MEETING_RESCHEDULE].append(
                    "meeting keywords + active meeting -> reschedule"
                )

        # ── Signal 7: Chat history patterns ───────────────────────────
        recent_messages = ctx.chat_history[-6:] if len(ctx.chat_history) > 6 else ctx.chat_history
        knowledge_questions = sum(
            1 for m in recent_messages
            if m.get("role") == "user" and _KNOWLEDGE_PATTERNS.search(m.get("content", ""))
        )
        if knowledge_questions >= 2:
            scores[ConversationStage.KNOWLEDGE] += 1.5
            reasons[ConversationStage.KNOWLEDGE].append(
                f"{knowledge_questions} knowledge questions in recent history"
            )

        # ── Compute winner ────────────────────────────────────────────
        # Remove UNKNOWN from contention (it's a fallback)
        scores[ConversationStage.UNKNOWN] = 0.0

        total_score = sum(max(s, 0) for s in scores.values())
        if total_score == 0:
            return StageClassification(
                stage=ConversationStage.DISCOVERY,
                confidence=0.5,
                reason="no signals detected, defaulting to DISCOVERY",
                scores=scores,
            )

        # Find the best stage
        best_stage = max(scores, key=lambda s: scores[s])
        best_score = scores[best_stage]
        confidence = best_score / total_score if total_score > 0 else 0.0

        # Build reason string
        reason_parts = reasons.get(best_stage, [])
        reason_str = "; ".join(reason_parts) if reason_parts else "aggregate scoring"

        # ── Confidence gate ───────────────────────────────────────────
        if confidence < CONFIDENCE_THRESHOLD:
            # Fall back to current stage or DISCOVERY
            fallback = ctx.current_stage if ctx.current_stage != ConversationStage.UNKNOWN else ConversationStage.DISCOVERY
            return StageClassification(
                stage=fallback,
                confidence=confidence,
                reason=f"low confidence ({confidence:.2f}), staying at {fallback.value}",
                scores=scores,
            )

        return StageClassification(
            stage=best_stage,
            confidence=round(confidence, 3),
            reason=reason_str,
            scores=scores,
        )
