from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database.base import Base
import enum

class ConversationStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ESCALATED = "escalated"

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        Enum(ConversationStatus, values_callable=lambda x: [e.value for e in x]),
        default=ConversationStatus.ACTIVE,
    )
    escalated = Column(Boolean, default=False)
    escalation_reason = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    message_count = Column(Integer, default=0)
    language = Column(String, nullable=True)
    model_used = Column(String, nullable=True)
    stt_model = Column(String, nullable=True)
    tts_model = Column(String, nullable=True)
    rag_enabled = Column(Boolean, default=True)
    ended_reason = Column(String, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    
    lead = relationship("Lead", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    summary = relationship("ConversationSummary", uselist=False, back_populates="conversation", cascade="all, delete-orphan")