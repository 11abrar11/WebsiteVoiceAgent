"""
Meeting Engine – business logic for scheduling meetings.
Generates available slots dynamically from business hours minus existing bookings.
"""
from datetime import date, time, timedelta, datetime
from app.repositories.meeting_repo import MeetingRepository
from app.models.meeting import MeetingStatus


# Standard business hours (configurable)
BUSINESS_HOURS_START = 10  # 10 AM
BUSINESS_HOURS_END = 17    # 5 PM (last slot at 4 PM)
SLOT_DURATION_HOURS = 1
DAYS_AHEAD = 7  # Offer slots for the next 7 business days


class MeetingEngine:

    def __init__(self, meeting_repo: MeetingRepository):
        self.repo = meeting_repo

    async def get_available_times(self) -> list[dict]:
        """
        Returns a list of available meeting times for the next N business days.
        Format: [{"date": "2026-07-01", "day": "Tuesday", "time": "10:00 AM"}, ...]
        """
        available = []
        today = date.today()
        
        start_date = today + timedelta(days=1)
        end_date = today + timedelta(days=DAYS_AHEAD + 7)
        
        # Phase 1: Eliminate N+1 queries by fetching all meetings in one round-trip
        all_meetings = await self.repo.get_meetings_in_range(start_date, end_date)
        
        # Build in-memory lookup for O(1) checks
        booked_times_by_date = {}
        for m in all_meetings:
            if m.status in [MeetingStatus.RESERVED, MeetingStatus.CONFIRMED]:
                if m.date not in booked_times_by_date:
                    booked_times_by_date[m.date] = set()
                booked_times_by_date[m.date].add(m.time)

        for day_offset in range(1, DAYS_AHEAD + 7):  # Check enough days to find N business days
            check_date = today + timedelta(days=day_offset)

            # Skip weekends (5 = Saturday, 6 = Sunday)
            if check_date.weekday() >= 5:
                continue

            booked_times = booked_times_by_date.get(check_date, set())

            # Generate all possible slots for this day
            for hour in range(BUSINESS_HOURS_START, BUSINESS_HOURS_END):
                slot_time = time(hour=hour, minute=0)
                if slot_time not in booked_times:
                    available.append({
                        "date": check_date.isoformat(),
                        "day": check_date.strftime("%A"),
                        "time": datetime.combine(check_date, slot_time).strftime("%I:%M %p"),
                        "time_24h": slot_time.isoformat(),
                    })

            if len(available) >= 10:  # Cap at 10 options to keep it manageable
                break

        return available

    async def book(self, date_str: str, time_str: str, lead_id: int, notes: str = None):
        """
        Book a meeting at the given date and time for a lead.
        date_str: ISO format (e.g., "2026-07-01")
        time_str: 24h format (e.g., "10:00:00") or "10:00"
        Returns the Meeting object or None if slot is taken.
        """
        from datetime import date as date_type, time as time_type, datetime

        meeting_date = date_type.fromisoformat(date_str)

        # Robust time parsing using standard library
        try:
            parsed_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            try:
                parsed_time = datetime.strptime(time_str, "%H:%M:%S").time()
            except ValueError:
                try:
                    parsed_time = datetime.strptime(time_str.upper(), "%I:%M %p").time()
                except ValueError:
                    parsed_time = datetime.strptime(time_str.upper(), "%I %p").time()
            
        meeting_time = time_type(hour=parsed_time.hour, minute=parsed_time.minute)

        # The repository now handles atomic creation and booking in a single transaction
        return await self.repo.book_meeting(
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            lead_id=lead_id,
            notes=notes,
        )
