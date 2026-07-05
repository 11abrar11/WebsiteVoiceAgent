"""
Conversation Strategy — Determines conversational objectives.

Separate from the Policy Engine. The strategy answers:
  - What is the current conversational objective?
  - What is the next business objective?
  - Which CRM field should be collected next?
  - Should information collection pause?
  - Should the conversation transition toward booking?

The LLM receives this strategy as context and executes it naturally.
The backend decides the strategy. The LLM follows it.
"""
from dataclasses import dataclass, field
from app.policy.stage_engine import ConversationStage


@dataclass
class ConversationStrategyResult:
    """Strategic guidance injected into the LLM prompt."""
    current_objective: str            # What to focus on right now
    next_objective: str               # What to aim for next
    crm_field_to_collect: str | None  # The single most important field to collect
    should_pause_collection: bool     # True if user seems fatigued or resistant
    should_suggest_meeting: bool      # True if lead is qualified enough
    strategy_notes: list[str] = field(default_factory=list)  # For decision log


# ── CRM field priority order ─────────────────────────────────────────────
# Ordered by business value and conversational naturalness.
CRM_FIELD_PRIORITY = [
    "name",
    "requirement",
    "company",
    "industry",
    "budget",
    "timeline",
    "company_size",
    "monthly_leads",
    "decision_maker",
    "phone",
]

# Fields that should not be asked for directly (collect only if volunteered)
PASSIVE_FIELDS = {"phone", "monthly_leads", "company_size", "decision_maker"}

# Number of consecutive turns without a new field before pausing collection
COLLECTION_FATIGUE_THRESHOLD = 4


class ConversationStrategy:
    """
    Lightweight strategic advisor for conversation flow.
    Produces actionable guidance based on the conversation stage and lead state.
    """

    def evaluate(
        self,
        stage: ConversationStage,
        lead_known_fields: list[str],
        lead_declined_fields: list[str],
        turn_count: int,
        turns_since_last_extraction: int,
        has_active_meeting: bool,
        lead_completeness: float,
    ) -> ConversationStrategyResult:
        """
        Determine the conversational strategy for this turn.
        """
        notes: list[str] = []

        # ── Determine CRM field to collect ────────────────────────────
        crm_field = self._next_crm_field(lead_known_fields, lead_declined_fields)
        if crm_field:
            notes.append(f"Next CRM target: {crm_field}")

        # ── Should we pause collection? ───────────────────────────────
        should_pause = False
        if turns_since_last_extraction >= COLLECTION_FATIGUE_THRESHOLD:
            should_pause = True
            notes.append(
                f"Collection paused: {turns_since_last_extraction} turns without extraction"
            )

        # If we're in a knowledge or meeting stage, don't push CRM collection
        if stage in (
            ConversationStage.KNOWLEDGE,
            ConversationStage.MEETING_DISCUSSION,
            ConversationStage.MEETING_BOOKING,
            ConversationStage.MEETING_RESCHEDULE,
        ):
            should_pause = True
            notes.append(f"Collection paused: stage {stage.value} takes priority")

        if should_pause:
            crm_field = None

        # ── Should we suggest a meeting? ──────────────────────────────
        should_suggest_meeting = (
            not has_active_meeting
            and lead_completeness >= 0.35
            and turn_count >= 4
            and stage not in (
                ConversationStage.GREETING,
                ConversationStage.MEETING_DISCUSSION,
                ConversationStage.MEETING_BOOKING,
                ConversationStage.MEETING_RESCHEDULE,
                ConversationStage.CLOSING,
            )
        )
        if should_suggest_meeting:
            notes.append("Lead is qualified -- meeting suggestion appropriate")

        # ── Determine objectives ──────────────────────────────────────
        current_objective, next_objective = self._get_objectives(
            stage, crm_field, should_suggest_meeting, has_active_meeting
        )

        return ConversationStrategyResult(
            current_objective=current_objective,
            next_objective=next_objective,
            crm_field_to_collect=crm_field,
            should_pause_collection=should_pause,
            should_suggest_meeting=should_suggest_meeting,
            strategy_notes=notes,
        )

    def _next_crm_field(
        self,
        known: list[str],
        declined: list[str],
    ) -> str | None:
        """
        Return the next CRM field to collect, respecting priority order.
        Skips known and declined fields. For passive fields, only suggest
        them if no active fields remain.
        """
        active_candidates = []
        passive_candidates = []

        for f in CRM_FIELD_PRIORITY:
            if f in known or f in declined:
                continue
            if f in PASSIVE_FIELDS:
                passive_candidates.append(f)
            else:
                active_candidates.append(f)

        if active_candidates:
            return active_candidates[0]
        if passive_candidates:
            return passive_candidates[0]
        return None

    def _get_objectives(
        self,
        stage: ConversationStage,
        crm_field: str | None,
        suggest_meeting: bool,
        has_meeting: bool,
    ) -> tuple[str, str]:
        """Return (current_objective, next_objective) based on stage."""

        objectives = {
            ConversationStage.GREETING: (
                "Welcome the user warmly and understand why they're reaching out",
                "Transition to learning about their needs",
            ),
            ConversationStage.DISCOVERY: (
                "Understand the user's needs and goals",
                f"Collect {crm_field}" if crm_field else "Explore their business context",
            ),
            ConversationStage.BUSINESS_DISCOVERY: (
                "Understand their business context, industry, and company",
                f"Collect {crm_field}" if crm_field else "Move toward qualification",
            ),
            ConversationStage.QUALIFICATION: (
                "Understand budget, timeline, and decision-making process",
                "Suggest scheduling a meeting" if not has_meeting else "Continue the conversation",
            ),
            ConversationStage.KNOWLEDGE: (
                "Answer the user's questions about our services using the knowledge base",
                "Circle back to understanding their specific needs",
            ),
            ConversationStage.MEETING_DISCUSSION: (
                "Help the user find a suitable meeting time",
                "Confirm the meeting slot",
            ),
            ConversationStage.MEETING_BOOKING: (
                "Confirm and book the selected meeting time",
                "Wrap up the conversation positively",
            ),
            ConversationStage.MEETING_RESCHEDULE: (
                "Help the user reschedule their existing meeting",
                "Confirm the new meeting time",
            ),
            ConversationStage.CLOSING: (
                "End the conversation warmly and professionally",
                "Ensure the user knows how to reach us again",
            ),
            ConversationStage.UNKNOWN: (
                "Understand what the user needs",
                "Guide the conversation toward their goals",
            ),
        }

        current, nxt = objectives.get(
            stage,
            ("Continue the conversation naturally", "Understand the user's needs"),
        )

        # Override next_objective if meeting suggestion is appropriate
        if suggest_meeting and stage not in (
            ConversationStage.MEETING_DISCUSSION,
            ConversationStage.MEETING_BOOKING,
            ConversationStage.CLOSING,
        ):
            nxt = "Naturally suggest scheduling a meeting with our team"

        return current, nxt
