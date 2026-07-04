import asyncio
import os
from datetime import date, time
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Date, Time, Enum, ForeignKey
from app.models.meeting import Meeting, MeetingStatus

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        from app.database.base import Base
        await conn.run_sync(Base.metadata.create_all)
        
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    from app.repositories.meeting_repo import MeetingRepository
    
    async with session_factory() as session:
        repo = MeetingRepository(session)
        try:
            slot = await repo.book_meeting(date(2026, 7, 6), time(10, 0), lead_id=1, notes="Test")
            print("Booked:", slot.id, slot.status)
        except Exception as e:
            print("Exception during booking:", type(e), e)

if __name__ == "__main__":
    asyncio.run(main())