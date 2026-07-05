"""
Tool Gate — Maps conversation stages to allowed tool schemas.

The LLM physically cannot call tools that are not exposed.
This module filters TOOL_DEFINITIONS based on the current stage
and meeting state.
"""
from app.policy.stage_engine import ConversationStage
from app.tools.tools import ALL_TOOL_DEFINITIONS


# ── Stage → Tool Name Mapping ─────────────────────────────────────────────
# Each stage lists the tool names that should be exposed to the LLM.

STAGE_TOOL_MAP: dict[ConversationStage, list[str]] = {
    ConversationStage.GREETING:           ["extract_lead_info"],
    ConversationStage.DISCOVERY:          ["extract_lead_info"],
    ConversationStage.BUSINESS_DISCOVERY: ["extract_lead_info"],
    ConversationStage.QUALIFICATION:      ["extract_lead_info"],
    ConversationStage.KNOWLEDGE:          ["search_knowledge_base", "extract_lead_info"],
    ConversationStage.MEETING_DISCUSSION: ["get_available_meeting_times", "extract_lead_info"],
    ConversationStage.MEETING_BOOKING:    ["confirm_meeting_slot", "extract_lead_info"],
    ConversationStage.MEETING_RESCHEDULE: ["confirm_meeting_slot", "extract_lead_info"],
    ConversationStage.CLOSING:            ["extract_lead_info"],
    ConversationStage.UNKNOWN:            ["extract_lead_info", "search_knowledge_base"],
}


class ToolGate:
    """
    Determines which tool schemas are exposed to the LLM for a given stage.
    Returns filtered tool definitions (full schema objects, not just names).
    """

    def get_allowed_tools(
        self,
        stage: ConversationStage,
        has_active_meeting: bool = False,
    ) -> list[dict]:
        """
        Return the list of tool schema dicts allowed for this stage.
        Applies additional business rules on top of the stage mapping.
        """
        allowed_names = list(STAGE_TOOL_MAP.get(stage, ["extract_lead_info"]))

        # ── Business rule: If active meeting exists, block new booking ──
        if has_active_meeting and "confirm_meeting_slot" in allowed_names:
            # In MEETING_RESCHEDULE stage, the tool stays but the backend
            # handles it as a reschedule. In MEETING_BOOKING, we should
            # redirect to MEETING_RESCHEDULE, but if the stage engine
            # already set it correctly, this is a no-op.
            pass  # confirm_meeting_slot handles both booking and reschedule

        # ── Filter ALL_TOOL_DEFINITIONS to only include allowed tools ──
        return [
            tool for tool in ALL_TOOL_DEFINITIONS
            if tool["function"]["name"] in allowed_names
        ]

    def get_allowed_tool_names(self, stage: ConversationStage) -> list[str]:
        """Return just the tool names for logging/debugging."""
        return list(STAGE_TOOL_MAP.get(stage, ["extract_lead_info"]))

    def explain_tool_exposure(
        self,
        stage: ConversationStage,
        has_active_meeting: bool = False,
    ) -> dict[str, str]:
        """
        Return a dict of {tool_name: reason} explaining why each tool
        is exposed. Used by the decision logger.
        """
        explanations = {}
        allowed = self.get_allowed_tools(stage, has_active_meeting)

        for tool in allowed:
            name = tool["function"]["name"]
            if name == "extract_lead_info":
                explanations[name] = "Always available for lead data collection"
            elif name == "search_knowledge_base":
                explanations[name] = f"Enabled because stage is {stage.value}"
            elif name == "get_available_meeting_times":
                explanations[name] = f"Enabled because stage is {stage.value}"
            elif name == "confirm_meeting_slot":
                if has_active_meeting:
                    explanations[name] = "Active meeting exists -- will reschedule"
                else:
                    explanations[name] = "No active meeting -- will book new"
            else:
                explanations[name] = f"Stage {stage.value} allows this tool"

        return explanations
