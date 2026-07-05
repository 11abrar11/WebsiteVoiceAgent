"""
Repository for meeting slot management and booking.
Meetings are linked to leads (not conversations).
"""
from datetime import date, time, datetime, timezone
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting, MeetingStatus


class MeetingRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_available_slots(self, for_date: date = None) -> list[Meeting]:
        """Get all available (unbooked) meeting slots, optionally filtered by date."""
        query = select(Meeting).where(Meeting.status == MeetingStatus.AVAILABLE)
        if for_date:
            query = query.where(Meeting.date == for_date)
        query = query.order_by(Meeting.date, Meeting.time)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_meetings_in_range(self, start_date: date, end_date: date) -> list[Meeting]:
        """Fetch ALL meetings (any status) within a date range in one query."""
        query = (
            select(Meeting)
            .where(
                and_(
                    Meeting.date >= start_date,
                    Meeting.date <= end_date
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def book_meeting(
        self,
        meeting_date: date,
        meeting_time: time,
        lead_id: int,
        notes: str = None,
    ) -> Meeting | None:
        """
        Book a meeting slot. Returns the Meeting if successful, None if already booked.
        Uses row-level locking to prevent race conditions.
        """
        # Select existing slot with lock to prevent race conditions
        result = await self.session.execute(
            select(Meeting).where(
                and_(
                    Meeting.date == meeting_date,
                    Meeting.time == meeting_time,
                )
            ).with_for_update()
        )
        slot = result.scalar_one_or_none()

        if slot:
            if slot.status != MeetingStatus.AVAILABLE:
                return None  # Slot already booked
            slot.status = MeetingStatus.RESERVED
            slot.lead_id = lead_id
            slot.notes = notes
            slot.updated_at = datetime.now(timezone.utc)
        else:
            # Slot doesn't exist, create it directly as Reserved
            slot = Meeting(
                date=meeting_date,
                time=meeting_time,
                status=MeetingStatus.RESERVED,
                lead_id=lead_id,
                notes=notes,
            )
            self.session.add(slot)

        await self.session.commit()
        await self.session.refresh(slot)
        return slot

    async def create_slot(self, slot_date: date, slot_time: time) -> Meeting:
        """Create a new available meeting slot."""
        meeting = Meeting(date=slot_date, time=slot_time, status=MeetingStatus.AVAILABLE)
        self.session.add(meeting)
        await self.session.commit()
        await self.session.refresh(meeting)
        return meeting

    async def get_all_meetings(self, limit: int = 50, offset: int = 0):
        """Get all booked meetings (non-Available) with lead info for the dashboard."""
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(Meeting)
            .options(selectinload(Meeting.lead))
            .where(Meeting.status != MeetingStatus.AVAILABLE)
            .order_by(Meeting.date.desc(), Meeting.time.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    # ── Policy Engine Support ─────────────────────────────────────────

    async def get_active_meeting_for_lead(self, lead_id: int) -> Meeting | None:
        """
        Get the active meeting (Reserved or Confirmed) for a lead.
        Returns None if no active meeting exists.
        Used by MeetingPolicy to enforce one-active-meeting-per-lead.
        """
        result = await self.session.execute(
            select(Meeting).where(
                and_(
                    Meeting.lead_id == lead_id,
                    Meeting.status.in_([
                        MeetingStatus.RESERVED,
                        MeetingStatus.CONFIRMED,
                    ]),
                )
            ).order_by(Meeting.date.desc(), Meeting.time.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def cancel_meeting(self, meeting_id: int) -> bool:
        """
        Cancel a meeting by ID. Sets status to Rescheduled.
        Returns True if successfully cancelled.
        """
        result = await self.session.execute(
            select(Meeting).where(Meeting.id == meeting_id)
        )
        meeting = result.scalar_one_or_none()
        if not meeting:
            return False

        meeting.status = MeetingStatus.RESCHEDULED
        meeting.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True

    async def count_past_meetings_for_lead(self, lead_id: int) -> int:
        """Count completed/cancelled/rescheduled meetings for analytics."""
        result = await self.session.execute(
            select(func.count(Meeting.id)).where(
                and_(
                    Meeting.lead_id == lead_id,
                    Meeting.status.in_([
                        MeetingStatus.COMPLETED,
                        MeetingStatus.CANCELLED,
                        MeetingStatus.RESCHEDULED,
                        MeetingStatus.NO_SHOW,
                    ]),
                )
            )
        )
        return result.scalar() or 0

