"""
Decision Logger — Full decision trace for every conversational turn.

In debug mode, generates a structured log entry explaining every backend
decision: stage classification, tool exposure, strategy, meeting policy,
RAG availability, and output validation.

Makes it possible to understand every backend decision without guessing.
"""
from dataclasses import dataclass, field
from app.policy.stage_engine import StageClassification, ConversationStage
from app.policy.conversation_strategy import ConversationStrategyResult
from app.policy.meeting_policy import MeetingPolicyResult
from app.policy.enterprise_policy import ValidationResult


@dataclass
class DecisionLog:
    """Complete decision trace for one conversational turn."""
    turn_number: int
    previous_stage: ConversationStage
    selected_stage: ConversationStage
    stage_confidence: float
    stage_reason: str
    lead_completeness: float
    lead_known_fields: list[str] = field(default_factory=list)
    lead_missing_fields: list[str] = field(default_factory=list)
    active_meeting_status: str = "None"
    available_tools: list[str] = field(default_factory=list)
    tool_exposure_reasons: dict[str, str] = field(default_factory=dict)
    rag_enabled: bool = False
    rag_reason: str = ""
    meeting_policy: str = ""
    strategy_objective: str = ""
    strategy_next: str = ""
    crm_target: str = "None"
    output_validation: str = "Not yet validated"
    output_violations: list[str] = field(default_factory=list)


class DecisionLogger:
    """
    Produces human-readable decision logs for debugging.
    Controlled by PERFORMANCE_PROFILING flag.
    """

    def create_log(
        self,
        turn_number: int,
        previous_stage: ConversationStage,
        stage_result: StageClassification,
        lead_completeness: float,
        lead_known_fields: list[str],
        lead_missing_fields: list[str],
        meeting_policy: MeetingPolicyResult,
        tool_names: list[str],
        tool_reasons: dict[str, str],
        rag_enabled: bool,
        strategy: ConversationStrategyResult,
    ) -> DecisionLog:
        """Build a DecisionLog from all the component outputs."""
        return DecisionLog(
            turn_number=turn_number,
            previous_stage=previous_stage,
            selected_stage=stage_result.stage,
            stage_confidence=stage_result.confidence,
            stage_reason=stage_result.reason,
            lead_completeness=lead_completeness,
            lead_known_fields=lead_known_fields,
            lead_missing_fields=lead_missing_fields,
            active_meeting_status=meeting_policy.policy_note,
            available_tools=tool_names,
            tool_exposure_reasons=tool_reasons,
            rag_enabled=rag_enabled,
            rag_reason="KNOWLEDGE stage or UNKNOWN stage" if rag_enabled else "Stage does not require RAG",
            meeting_policy=meeting_policy.policy_note,
            strategy_objective=strategy.current_objective,
            strategy_next=strategy.next_objective,
            crm_target=strategy.crm_field_to_collect or "None",
        )

    def update_output_validation(
        self,
        log: DecisionLog,
        validation: ValidationResult,
    ) -> DecisionLog:
        """Update the log with output validation results."""
        if validation.is_valid:
            log.output_validation = "PASSED"
        else:
            log.output_validation = "VIOLATIONS_DETECTED"
            log.output_violations = validation.violations
        return log

    def format_log(self, log: DecisionLog) -> str:
        """Format the decision log for console output."""
        lines = []
        lines.append("")
        lines.append("+" + "-" * 58 + "+")
        lines.append(f"| DECISION LOG - Turn {log.turn_number:<37d}|")
        lines.append("+" + "-" * 58 + "+")
        lines.append(f"| Previous Stage:    {log.previous_stage.value:<38s}|")
        lines.append(f"| Selected Stage:    {log.selected_stage.value:<38s}|")
        lines.append(f"| Confidence:        {log.stage_confidence:<38.3f}|")
        lines.append(f"| Reason:            {_trunc(log.stage_reason, 38):<38s}|")
        lines.append("+" + "-" * 58 + "+")
        lines.append(f"| Lead Completeness: {log.lead_completeness:<38.0%}|")
        lines.append(f"| Known Fields:      {_trunc(', '.join(log.lead_known_fields), 38):<38s}|")
        lines.append(f"| Missing Fields:    {_trunc(', '.join(log.lead_missing_fields), 38):<38s}|")
        lines.append("+" + "-" * 58 + "+")
        lines.append(f"| Active Meeting:    {_trunc(log.active_meeting_status, 38):<38s}|")
        lines.append(f"| Meeting Policy:    {_trunc(log.meeting_policy, 38):<38s}|")
        lines.append("+" + "-" * 58 + "+")
        lines.append(f"| Available Tools:   {_trunc(', '.join(log.available_tools), 38):<38s}|")
        for tool, reason in log.tool_exposure_reasons.items():
            lines.append(f"|   -> {tool:<15s} {_trunc(reason, 36):<36s}|")
        lines.append(f"| RAG Enabled:       {'Yes' if log.rag_enabled else 'No':<38s}|")
        lines.append(f"| RAG Reason:        {_trunc(log.rag_reason, 38):<38s}|")
        lines.append("+" + "-" * 58 + "+")
        lines.append(f"| Objective:         {_trunc(log.strategy_objective, 38):<38s}|")
        lines.append(f"| Next Objective:    {_trunc(log.strategy_next, 38):<38s}|")
        lines.append(f"| CRM Target:        {log.crm_target:<38s}|")
        lines.append("+" + "-" * 58 + "+")
        lines.append(f"| Output Validation: {log.output_validation:<38s}|")
        for v in log.output_violations:
            lines.append(f"|   ! {_trunc(v, 53):<53s}|")
        lines.append("+" + "-" * 58 + "+")
        lines.append("")

        return "\n".join(lines)


def _trunc(s: str, max_len: int) -> str:
    """Truncate a string to max_len, adding ... if needed."""
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."
