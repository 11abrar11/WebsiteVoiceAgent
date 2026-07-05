"""
Meeting Policy — Backend enforcement of meeting business rules.

Rules:
  - One active meeting per lead.
  - If an active meeting exists, new bookings are blocked → reschedule flow.
  - Completed/Cancelled/Rescheduled meetings remain for analytics.
  - The LLM never enforces these rules — the backend does.
"""
from dataclasses import dataclass
from app.database.connection import AsyncSessionLocal
from app.repositories.meeting_repo import MeetingRepository
from app.models.meeting import MeetingStatus


@dataclass
class MeetingPolicyResult:
    """Output of meeting policy evaluation."""
    has_active_meeting: bool
    active_meeting_id: int | None
    active_meeting_info: str | None   # Human-readable, e.g. "July 10 at 2:00 PM"
    can_book_new: bool                # True if no active meeting
    should_reschedule: bool           # True if active meeting exists
    past_meetings_count: int          # For analytics context
    policy_note: str                  # Explanation for the decision log


class MeetingPolicy:
    """Evaluates meeting business rules for a given lead."""

    async def evaluate(self, lead_id: int | None) -> MeetingPolicyResult:
        """
        Check the meeting state for a lead and return policy decisions.
        """
        if not lead_id:
            return MeetingPolicyResult(
                has_active_meeting=False,
                active_meeting_id=None,
                active_meeting_info=None,
                can_book_new=False,
                should_reschedule=False,
                past_meetings_count=0,
                policy_note="No lead ID -- meeting operations disabled",
            )

        async with AsyncSessionLocal() as session:
            repo = MeetingRepository(session)
            active = await repo.get_active_meeting_for_lead(lead_id)
            past_count = await repo.count_past_meetings_for_lead(lead_id)

        if active:
            # Format the active meeting info for context
            date_str = active.date.strftime("%B %d, %Y")
            time_str = active.time.strftime("%I:%M %p")
            meeting_info = f"{date_str} at {time_str}"

            return MeetingPolicyResult(
                has_active_meeting=True,
                active_meeting_id=active.id,
                active_meeting_info=meeting_info,
                can_book_new=False,
                should_reschedule=True,
                past_meetings_count=past_count,
                policy_note=f"Active meeting exists ({meeting_info}) -- booking blocked, reschedule available",
            )

        return MeetingPolicyResult(
            has_active_meeting=False,
            active_meeting_id=None,
            active_meeting_info=None,
            can_book_new=True,
            should_reschedule=False,
            past_meetings_count=past_count,
            policy_note="No active meeting -- booking allowed",
        )
