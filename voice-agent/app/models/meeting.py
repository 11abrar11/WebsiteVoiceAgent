"""
Meeting model – stores scheduled meetings between clients and the company.
Meetings belong to a Lead (not a Conversation) so they persist across sessions.
"""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, Time, Text, Integer, Float, DateTime, Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class MeetingStatus(str, enum.Enum):
    AVAILABLE = "Available"
    RESERVED = "Reserved"
    CONFIRMED = "Confirmed"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    RESCHEDULED = "Rescheduled"
    NO_SHOW = "No_Show"


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    status = Column(
        Enum(MeetingStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=MeetingStatus.AVAILABLE,
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    lead = relationship("Lead", back_populates="meetings")
