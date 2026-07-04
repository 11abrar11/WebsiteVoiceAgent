"""
Lead model – persistent client profile identified by email.
The email is the business-facing identifier; the integer `id` is the
internal primary key used across all services and relationships.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(300), nullable=True)
    industry = Column(String(200), nullable=True)
    requirement = Column(Text, nullable=True)
    monthly_leads = Column(String(100), nullable=True)
    company_size = Column(String(100), nullable=True)
    budget = Column(String(200), nullable=True)
    timeline = Column(String(200), nullable=True)
    decision_maker = Column(String(10), nullable=True)  # yes/no/unknown
    preferred_language = Column(String(50), nullable=True)  # future
    timezone = Column(String(50), nullable=True)  # future
    lead_score = Column(Integer, nullable=True, default=0)
    lead_status = Column(String(30), nullable=True, default="Cold")  # Cold, Warm, Hot
    data_completeness = Column(Float, nullable=True, default=0.0)
    last_contacted = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    conversations = relationship("Conversation", back_populates="lead", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="lead", cascade="all, delete-orphan")
