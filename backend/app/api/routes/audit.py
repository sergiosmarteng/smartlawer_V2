from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.models.audit_event import AuditEvent
from app.models.document import Document
from app.models.user import User
from app.schemas.audit import AuditEventResponse, OpsSummaryResponse

router = APIRouter()


@router.get("/audit", response_model=list[AuditEventResponse])
def list_audit_events(
    event_type: str | None = Query(default=None, max_length=80),
    entity_id: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=50, ge=1, le=200),
    scope: str = Query(default="own", pattern="^(own|all)$"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Queryable audit trail (C4 DoD).

    ``scope=own`` (default) returns the caller's events; ``scope=all``
    requires the admin role.
    """
    query = db.query(AuditEvent)
    if scope == "all":
        if (current_user.role or "user") != "admin":
            raise HTTPException(status_code=403, detail="Admin role required")
    else:
        query = query.filter(AuditEvent.user_id == current_user.id)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)
    return query.order_by(AuditEvent.created_at.desc()).limit(limit).all()


@router.get("/ops/summary", response_model=OpsSummaryResponse)
def ops_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
):
    """Platform overview (C4/BL-018): workflow states, 24h event counts,
    recent pipeline failures. Admin only."""
    del current_user

    status_rows = (
        db.query(Document.status, func.count(Document.id))
        .group_by(Document.status)
        .all()
    )
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    event_rows = (
        db.query(AuditEvent.event_type, func.count(AuditEvent.id))
        .filter(AuditEvent.created_at >= since)
        .group_by(AuditEvent.event_type)
        .all()
    )
    failures = (
        db.query(AuditEvent)
        .filter(AuditEvent.event_type == AuditEvent.DOCUMENT_FAILED)
        .order_by(AuditEvent.created_at.desc())
        .limit(10)
        .all()
    )
    return OpsSummaryResponse(
        documents_by_status={str(status or "unknown"): count for status, count in status_rows},
        events_24h={str(event): count for event, count in event_rows},
        recent_failures=failures,
    )
