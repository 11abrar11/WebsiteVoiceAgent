"""
Policy Engine — Central orchestrator that consults all policy components
and produces a unified PolicyDecision for each conversational turn.

This is NOT a God Object. It delegates to focused components:
  - StageEngine: determines conversation stage
  - ToolGate: determines allowed tools
  - MeetingPolicy: meeting business rules
  - ConversationStrategy: objectives and CRM guidance
  - EnterprisePolicy: input/output validation
  - DynamicPromptBuilder: prompt assembly
  - TokenProfiler: debug-mode profiling
  - DecisionLogger: debug-mode decision trace

Each component is independently testable.
"""
from dataclasses import dataclass, field
from app.policy.stage_engine import (
    StageEngine, StageContext, StageClassification, ConversationStage,
)
from app.policy.tool_gate import ToolGate
from app.policy.meeting_policy import MeetingPolicy, MeetingPolicyResult
from app.policy.conversation_strategy import (
    ConversationStrategy, ConversationStrategyResult,
)
from app.policy.enterprise_policy import EnterprisePolicy, ValidationResult
from app.policy.prompt_builder import DynamicPromptBuilder
from app.policy.token_profiler import TokenProfiler
from app.policy.decision_logger import DecisionLogger, DecisionLog


@dataclass
class PolicyDecision:
    """
    The complete output of a policy evaluation.
    ConversationManager consumes this to build and gate the LLM request.
    """
    # Stage
    stage: ConversationStage
    stage_confidence: float
    stage_reason: str

    # Prompt
    system_prompt: str

    # Tools
    allowed_tools: list[dict]           # Full tool schema dicts
    allowed_tool_names: list[str]       # Just names for quick checks

    # RAG
    rag_enabled: bool

    # Meeting
    meeting_policy: MeetingPolicyResult

    # Strategy
    strategy: ConversationStrategyResult

    # Debug
    decision_log: DecisionLog | None = None


class PolicyEngine:
    """
    Orchestrates all policy components to produce a PolicyDecision.
    Called by ConversationManager before every LLM request.
    """

    def __init__(self):
        self.stage_engine = StageEngine()
        self.tool_gate = ToolGate()
        self.meeting_policy = MeetingPolicy()
        self.strategy = ConversationStrategy()
        self.enterprise_policy = EnterprisePolicy()
        self.prompt_builder = DynamicPromptBuilder()
        self.token_profiler = TokenProfiler()
        self.decision_logger = DecisionLogger()

    async def evaluate(
        self,
        user_message: str,
        chat_history: list[dict],
        lead_state,                          # LeadStateManager
        lead_id: int | None,
        current_stage: ConversationStage,
        turn_count: int,
        returning_context: str,
        conversation_summary: str,
        turns_since_last_extraction: int,
        debug: bool = False,
    ) -> PolicyDecision:
        """
        Evaluate all policies and return a unified decision.
        """
        self.token_profiler.reset()
        self.token_profiler.start_prompt_build()

        # ── 1. Compute lead state metrics ─────────────────────────────
        known_fields = []
        missing_fields = []
        declined_fields = []
        for field_name, data in lead_state.state.items():
            if data["status"] in ("KNOWN", "INFERRED"):
                known_fields.append(field_name)
            elif data["status"] == "DECLINED":
                declined_fields.append(field_name)
            else:
                missing_fields.append(field_name)

        lead_completeness = len(known_fields) / max(len(lead_state.state), 1)

        # ── 2. Evaluate meeting policy ────────────────────────────────
        meeting_result = await self.meeting_policy.evaluate(lead_id)

        # ── 3. Extract previous tool calls from history ───────────────
        previous_tools = []
        for msg in chat_history:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    name = tc.get("function", {}).get("name", "") if isinstance(tc, dict) else ""
                    if name:
                        previous_tools.append(name)

        # ── 4. Classify conversation stage ────────────────────────────
        stage_ctx = StageContext(
            current_stage=current_stage,
            turn_count=turn_count,
            user_message=user_message,
            chat_history=chat_history,
            lead_known_count=len(known_fields),
            lead_total_fields=len(lead_state.state),
            lead_declined_fields=declined_fields,
            has_active_meeting=meeting_result.has_active_meeting,
            active_meeting_info=meeting_result.active_meeting_info,
            previous_tool_calls=previous_tools,
            rag_was_invoked="search_knowledge_base" in previous_tools,
        )
        stage_result = self.stage_engine.classify(stage_ctx)

        # ── 5. Gate tools ─────────────────────────────────────────────
        allowed_tools = self.tool_gate.get_allowed_tools(
            stage_result.stage,
            has_active_meeting=meeting_result.has_active_meeting,
        )
        allowed_tool_names = [t["function"]["name"] for t in allowed_tools]
        tool_reasons = self.tool_gate.explain_tool_exposure(
            stage_result.stage,
            has_active_meeting=meeting_result.has_active_meeting,
        )

        # ── 6. Determine RAG availability ─────────────────────────────
        rag_enabled = "search_knowledge_base" in allowed_tool_names

        # ── 7. Evaluate conversation strategy ─────────────────────────
        strategy_result = self.strategy.evaluate(
            stage=stage_result.stage,
            lead_known_fields=known_fields,
            lead_declined_fields=declined_fields,
            turn_count=turn_count,
            turns_since_last_extraction=turns_since_last_extraction,
            has_active_meeting=meeting_result.has_active_meeting,
            lead_completeness=lead_completeness,
        )

        # ── 8. Build dynamic prompt ───────────────────────────────────
        lead_context = lead_state.get_prompt_context()
        meeting_context = meeting_result.active_meeting_info if meeting_result.has_active_meeting else None

        system_prompt = self.prompt_builder.build(
            stage=stage_result.stage,
            lead_context=lead_context,
            conversation_summary=returning_context + ("\n" + conversation_summary if conversation_summary else ""),
            strategy=strategy_result,
            meeting_context=meeting_context,
        )

        self.token_profiler.end_prompt_build()
        self.token_profiler.set_prompt_sections(self.prompt_builder.get_section_breakdown())
        self.token_profiler.set_tool_schemas(allowed_tools)

        # ── 9. Build decision log ─────────────────────────────────────
        decision_log = None
        if debug:
            decision_log = self.decision_logger.create_log(
                turn_number=turn_count,
                previous_stage=current_stage,
                stage_result=stage_result,
                lead_completeness=lead_completeness,
                lead_known_fields=known_fields,
                lead_missing_fields=missing_fields,
                meeting_policy=meeting_result,
                tool_names=allowed_tool_names,
                tool_reasons=tool_reasons,
                rag_enabled=rag_enabled,
                strategy=strategy_result,
            )

        return PolicyDecision(
            stage=stage_result.stage,
            stage_confidence=stage_result.confidence,
            stage_reason=stage_result.reason,
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            allowed_tool_names=allowed_tool_names,
            rag_enabled=rag_enabled,
            meeting_policy=meeting_result,
            strategy=strategy_result,
            decision_log=decision_log,
        )

    def validate_output(
        self,
        response: str,
        rag_was_invoked: bool = False,
    ) -> ValidationResult:
        """Delegate output validation to EnterprisePolicy."""
        return self.enterprise_policy.validate_output(response, rag_was_invoked)

    def validate_tool_call(
        self,
        tool_name: str,
        tool_args: dict,
        allowed_tool_names: list[str],
    ) -> tuple[bool, str]:
        """Delegate tool call validation to EnterprisePolicy."""
        return self.enterprise_policy.validate_tool_call(
            tool_name, tool_args, allowed_tool_names,
        )
