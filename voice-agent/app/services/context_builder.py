"""
ContextBuilder – assembles LLM prompt context from lead profile and
conversation history.  Keeps prompts compact and structured so that
ConversationManager stays focused on orchestration.
"""
from app.database.connection import AsyncSessionLocal
from app.repositories.conversation_repo import ConversationRepository


class ContextBuilder:
    """Stateless service for building LLM context strings."""

    RETURNING_USER_TEMPLATE = (
        "RETURNING CLIENT CONTEXT:\n"
        "- Name: {name}\n"
        "- Email: {email}\n"
        "- Phone: {phone}\n"
        "- Company: {company}\n"
        "- Industry: {industry}\n"
        "- Requirement: {requirement}\n"
        "- Budget: {budget}\n"
        "- Timeline: {timeline}\n"
        "- Decision Maker: {decision_maker}\n"
        "- Lead Status: {lead_status}\n"
        "- Fields still missing: {missing_fields}\n"
        "\n"
        "PREVIOUS INTERACTION SUMMARIES:\n"
        "{summaries}\n"
        "\n"
        "IMPORTANT: Do NOT re-ask for information already collected above. "
        "Continue the conversation naturally, building on what you already know.\n"
    )

    async def build(self, lead_id: int | None) -> str:
        """
        Build the returning-user context block for injection into the system prompt.
        Returns an empty string for new / unknown leads.
        """
        if lead_id is None:
            return ""

        async with AsyncSessionLocal() as session:
            repo = ConversationRepository(session)
            profile = await repo.get_lead_profile(lead_id)
            summaries = await repo.get_recent_summaries(lead_id, limit=3)

        if not profile:
            return ""

        # Only inject context if the lead has at least one filled field
        # (beyond the email which is always present)
        has_data = any(
            profile.get(f)
            for f in ["name", "phone", "company", "industry", "requirement",
                       "budget", "timeline", "decision_maker"]
        )
        has_summaries = bool(summaries)

        if not has_data and not has_summaries:
            return ""

        # Format missing fields
        missing = profile.get("missing_fields", [])
        missing_str = ", ".join(missing) if missing else "None"

        # Format summaries
        if summaries:
            summary_lines = []
            for i, s in enumerate(summaries, 1):
                summary_lines.append(f"  Session {i}: {s}")
            summaries_str = "\n".join(summary_lines)
        else:
            summaries_str = "  No previous sessions recorded."

        return self.RETURNING_USER_TEMPLATE.format(
            name=profile.get("name") or "Unknown",
            email=profile.get("email") or "Unknown",
            phone=profile.get("phone") or "Not provided",
            company=profile.get("company") or "Not provided",
            industry=profile.get("industry") or "Not provided",
            requirement=profile.get("requirement") or "Not discussed",
            budget=profile.get("budget") or "Not discussed",
            timeline=profile.get("timeline") or "Not discussed",
            decision_maker=profile.get("decision_maker") or "Unknown",
            lead_status=profile.get("lead_status") or "Cold",
            missing_fields=missing_str,
            summaries=summaries_str,
        )


# Module-level singleton
context_builder = ContextBuilder()
