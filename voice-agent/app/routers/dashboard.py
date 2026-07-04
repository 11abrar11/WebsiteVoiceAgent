"""
Dashboard router – protected API endpoints for the admin dashboard.
Updated for lead-centric integer-PK schema.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_session
from app.models.admin import Admin
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.meeting_repo import MeetingRepository
from app.services.auth_service import get_current_admin

router = APIRouter()


@router.get("/conversations")
async def list_conversations(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    admin: Admin = Depends(get_current_admin),
):
    """Get a paginated list of all conversations."""
    repo = ConversationRepository(session)
    conversations = await repo.get_all_conversations(limit=limit, offset=offset)
    total = await repo.count_conversations()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "conversations": [
            {
                "id": c.id,
                "email": c.lead.email if c.lead else None,
                "started_at": c.started_at.isoformat() if c.started_at else None,
                "ended_at": c.ended_at.isoformat() if c.ended_at else None,
                "status": c.status.value if c.status else None,
                "duration_seconds": c.duration_seconds,
                "message_count": c.message_count,
                "escalated": c.escalated,
                "lead": {
                    "name": c.lead.name,
                    "company": c.lead.company,
                    "email": c.lead.email,
                    "phone": c.lead.phone,
                    "lead_score": c.lead.lead_score,
                    "lead_status": c.lead.lead_status,
                } if c.lead else None,
                "summary": c.summary.summary if c.summary else None,
            }
            for c in conversations
        ],
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation_detail(
    conversation_id: int,
    session: AsyncSession = Depends(get_session),
    admin: Admin = Depends(get_current_admin),
):
    """Get full details of a single conversation including transcript."""
    repo = ConversationRepository(session)
    conv = await repo.get_conversation(conversation_id)

    if not conv:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conv.id,
        "started_at": conv.started_at.isoformat() if conv.started_at else None,
        "ended_at": conv.ended_at.isoformat() if conv.ended_at else None,
        "status": conv.status.value if conv.status else None,
        "duration_seconds": conv.duration_seconds,
        "message_count": conv.message_count,
        "model_used": conv.model_used,
        "escalated": conv.escalated,
        "escalation_reason": conv.escalation_reason,
        "lead": {
            "id": conv.lead.id,
            "email": conv.lead.email,
            "name": conv.lead.name,
            "phone": conv.lead.phone,
            "company": conv.lead.company,
            "industry": conv.lead.industry,
            "requirement": conv.lead.requirement,
            "monthly_leads": conv.lead.monthly_leads,
            "company_size": conv.lead.company_size,
            "budget": conv.lead.budget,
            "timeline": conv.lead.timeline,
            "decision_maker": conv.lead.decision_maker,
            "lead_score": conv.lead.lead_score,
            "lead_status": conv.lead.lead_status,
            "data_completeness": conv.lead.data_completeness,
        } if conv.lead else None,
        "summary": {
            "text": conv.summary.summary,
            "model": conv.summary.summary_model,
            "version": conv.summary.summary_version,
            "generated_at": conv.summary.generated_at.isoformat() if conv.summary.generated_at else None,
        } if conv.summary else None,
        "messages": [
            {
                "id": m.id,
                "speaker": m.speaker,
                "content": m.content,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                "message_type": m.message_type,
            }
            for m in sorted(conv.messages, key=lambda x: x.timestamp)
        ],
    }


@router.get("/meetings")
async def list_meetings(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    admin: Admin = Depends(get_current_admin),
):
    """Get all booked meetings for the dashboard."""
    repo = MeetingRepository(session)
    meetings = await repo.get_all_meetings(limit=limit, offset=offset)

    return {
        "meetings": [
            {
                "id": m.id,
                "date": m.date.isoformat() if m.date else None,
                "time": m.time.isoformat() if m.time else None,
                "status": m.status.value if m.status else None,
                "notes": m.notes,
                "email": m.lead.email if m.lead else None,
                "lead_name": m.lead.name if m.lead else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in meetings
        ],
    }
