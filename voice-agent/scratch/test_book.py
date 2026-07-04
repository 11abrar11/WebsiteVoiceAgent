import asyncio
from datetime import date, time
from app.database.connection import AsyncSessionLocal
from app.repositories.meeting_repo import MeetingRepository
from app.meeting.engine import MeetingEngine

async def test_booking():
    async with AsyncSessionLocal() as session:
        repo = MeetingRepository(session)
        engine = MeetingEngine(repo)
        
        # Test lead ID 1
        meeting = await engine.book("2026-07-06", "10:00:00", lead_id=1, notes="Test booking")
        if meeting:
            print(f"Meeting booked! ID: {meeting.id}, Date: {meeting.date}, Time: {meeting.time}, Lead: {meeting.lead_id}, Status: {meeting.status}")
        else:
            print("Failed to book meeting.")

if __name__ == "__main__":
    asyncio.run(test_booking())
