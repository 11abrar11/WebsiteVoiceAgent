"""
Token Profiler — Debug-mode per-section token breakdown logger.

Reports:
  - Tokens consumed by each prompt section (estimated)
  - Tokens consumed by each tool schema (estimated)
  - Number of exposed tools
  - Number of retrieved documents
  - Prompt build time
  - LLM latency
  - Tool execution latency
  - Total prompt tokens (from API)
  - Completion tokens (from API)

Uses the Groq API's usage stats for totals, and distributes proportionally
across sections using character counts for per-section estimates.
"""
import time
from dataclasses import dataclass, field


# Rough token-to-char ratio for LLaMA tokenizers (English text)
_CHARS_PER_TOKEN = 4.0


@dataclass
class TokenReport:
    """Complete token profiling report for a single turn."""
    # From API
    total_prompt_tokens: int = 0
    completion_tokens: int = 0

    # Per-section estimates
    section_breakdown: dict[str, int] = field(default_factory=dict)

    # Per-tool-schema estimates
    tool_schema_breakdown: dict[str, int] = field(default_factory=dict)

    # Metadata
    num_exposed_tools: int = 0
    num_retrieved_docs: int = 0
    prompt_build_time_ms: float = 0.0
    llm_latency_ms: float = 0.0
    tool_exec_latency_ms: float = 0.0

    # Was this a double-request turn (tool call)?
    is_tool_call_turn: bool = False
    second_request_tokens: int = 0


class TokenProfiler:
    """
    Collects timing and token data throughout a turn, then produces
    a formatted report.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all collected data for a new turn."""
        self._prompt_build_start: float | None = None
        self._prompt_build_end: float | None = None
        self._prompt_sections: list[tuple[str, str]] = []
        self._tool_schemas: list[dict] = []
        self._api_prompt_tokens: int = 0
        self._api_completion_tokens: int = 0
        self._second_request_tokens: int = 0
        self._is_tool_call_turn: bool = False
        self._llm_latency_ms: float = 0.0
        self._tool_exec_latency_ms: float = 0.0
        self._num_retrieved_docs: int = 0

    def start_prompt_build(self):
        self._prompt_build_start = time.perf_counter()

    def end_prompt_build(self):
        self._prompt_build_end = time.perf_counter()

    def set_prompt_sections(self, sections: list[tuple[str, str]]):
        """Store the (section_name, content) pairs from the prompt builder."""
        self._prompt_sections = sections

    def set_tool_schemas(self, tools: list[dict]):
        """Store the tool schemas that were exposed."""
        self._tool_schemas = tools

    def set_api_usage(self, prompt_tokens: int, completion_tokens: int):
        """Store the token counts from the Groq API response."""
        self._api_prompt_tokens = prompt_tokens
        self._api_completion_tokens = completion_tokens

    def set_second_request_tokens(self, prompt_tokens: int):
        """Store token count from the second LLM request (after tool call)."""
        self._second_request_tokens = prompt_tokens
        self._is_tool_call_turn = True

    def set_llm_latency(self, latency_ms: float):
        self._llm_latency_ms = latency_ms

    def set_tool_exec_latency(self, latency_ms: float):
        self._tool_exec_latency_ms = latency_ms

    def set_num_retrieved_docs(self, count: int):
        self._num_retrieved_docs = count

    def generate_report(self) -> TokenReport:
        """Generate the final token report for this turn."""
        report = TokenReport()
        report.total_prompt_tokens = self._api_prompt_tokens
        report.completion_tokens = self._api_completion_tokens
        report.num_exposed_tools = len(self._tool_schemas)
        report.num_retrieved_docs = self._num_retrieved_docs
        report.is_tool_call_turn = self._is_tool_call_turn
        report.second_request_tokens = self._second_request_tokens
        report.llm_latency_ms = self._llm_latency_ms
        report.tool_exec_latency_ms = self._tool_exec_latency_ms

        # Prompt build time
        if self._prompt_build_start and self._prompt_build_end:
            report.prompt_build_time_ms = (
                (self._prompt_build_end - self._prompt_build_start) * 1000
            )

        # ── Estimate per-section token counts ─────────────────────────
        # Calculate character counts for each section
        section_chars = {}
        total_section_chars = 0
        for name, content in self._prompt_sections:
            chars = len(content)
            section_chars[name] = chars
            total_section_chars += chars

        # Calculate tool schema character counts
        tool_chars = {}
        total_tool_chars = 0
        for tool in self._tool_schemas:
            name = tool["function"]["name"]
            chars = len(str(tool))
            tool_chars[name] = chars
            total_tool_chars += chars

        # Proportionally distribute API-reported prompt tokens
        total_chars = total_section_chars + total_tool_chars
        if total_chars > 0 and self._api_prompt_tokens > 0:
            # Reserve some tokens for chat history (not in sections)
            # Estimate: total_api - estimated_prompt ≈ history tokens
            estimated_prompt_chars = total_chars
            estimated_prompt_tokens = int(estimated_prompt_chars / _CHARS_PER_TOKEN)

            for name, chars in section_chars.items():
                report.section_breakdown[name] = int(chars / _CHARS_PER_TOKEN)

            for name, chars in tool_chars.items():
                report.tool_schema_breakdown[name] = int(chars / _CHARS_PER_TOKEN)

            # Remaining tokens are attributed to chat history
            accounted = sum(report.section_breakdown.values()) + sum(report.tool_schema_breakdown.values())
            history_tokens = max(0, self._api_prompt_tokens - accounted)
            report.section_breakdown["chat_history"] = history_tokens

        return report

    def format_report(self, report: TokenReport) -> str:
        """Format the report as a human-readable string for logging."""
        lines = []
        lines.append("")
        lines.append("=" * 55)
        lines.append(" TOKEN PROFILER REPORT")
        lines.append("=" * 55)

        # Section breakdown
        lines.append(" Prompt Sections:")
        for name, tokens in report.section_breakdown.items():
            lines.append(f"   {name:<25s} ~{tokens:>4d} tokens")

        if report.tool_schema_breakdown:
            lines.append(" Tool Schemas:")
            for name, tokens in report.tool_schema_breakdown.items():
                lines.append(f"   {name:<25s} ~{tokens:>4d} tokens")

        lines.append(" -" * 27)
        lines.append(f" Total Prompt Tokens:       {report.total_prompt_tokens:>5d}")
        lines.append(f" Completion Tokens:         {report.completion_tokens:>5d}")

        if report.is_tool_call_turn:
            lines.append(f" 2nd Request Tokens:        {report.second_request_tokens:>5d}")
            lines.append(f" Combined Prompt Tokens:    {report.total_prompt_tokens + report.second_request_tokens:>5d}")

        lines.append(" -" * 27)
        lines.append(f" Exposed Tools:             {report.num_exposed_tools:>5d}")
        lines.append(f" Retrieved Docs:            {report.num_retrieved_docs:>5d}")
        lines.append(f" Prompt Build Time:       {report.prompt_build_time_ms:>6.1f} ms")
        lines.append(f" LLM Latency:             {report.llm_latency_ms:>6.1f} ms")
        lines.append(f" Tool Exec Latency:       {report.tool_exec_latency_ms:>6.1f} ms")
        lines.append("=" * 55)
        lines.append("")

        return "\n".join(lines)
