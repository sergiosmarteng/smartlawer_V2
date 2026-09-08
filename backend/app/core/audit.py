"""Audit-trail helpers (C4/BL-018 + BL-024).

All helpers are best-effort: audit must never break the audited action.
"""
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent

logger = logging.getLogger(__name__)


def record_audit(
    db: Session,
    *,
    event_type: str,
    user_id=None,
    entity_type: str | None = None,
    entity_id: Any | None = None,
    meta: dict | None = None,
) -> None:
    try:
        db.add(
            AuditEvent(
                user_id=user_id,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                meta=meta or {},
            )
        )
        db.commit()
    except Exception as exc:
        logger.warning("Audit record failed (%s): %s", event_type, exc)
        try:
            db.rollback()
        except Exception:
            pass


def audit_document_completion(db: Session, *, document) -> None:
    """Completion/failure audit with workflow timing (C4/BL-018).

    ``document`` needs: id, user_id, status, status_detail, error_message,
    uploaded_at, completed_at. Never raises.
    """
    try:
        from app.models.document import Document

        duration_ms = None
        if document.uploaded_at and document.completed_at:
            duration_ms = int(
                (document.completed_at - document.uploaded_at).total_seconds() * 1000
            )
        if document.status == Document.STATUS_COMPLETED:
            record_audit(
                db,
                event_type=AuditEvent.DOCUMENT_COMPLETED,
                user_id=document.user_id,
                entity_type="document",
                entity_id=document.id,
                meta={
                    "duration_ms": duration_ms,
                    "status_detail": document.status_detail,
                },
            )
        elif document.status == Document.STATUS_ERROR:
            record_audit(
                db,
                event_type=AuditEvent.DOCUMENT_FAILED,
                user_id=document.user_id,
                entity_type="document",
                entity_id=document.id,
                meta={
                    "duration_ms": duration_ms,
                    "status_detail": document.status_detail,
                    "error": (document.error_message or "")[:500],
                },
            )
    except Exception as exc:
        logger.warning("Completion audit failed: %s", exc)
