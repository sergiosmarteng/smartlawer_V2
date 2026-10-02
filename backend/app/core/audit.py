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


_SENSITIVE_KEYS = ("snippet", "prompt", "api_key", "token", "secret", "password")


def sanitize_meta(meta: dict | None) -> dict:
    """Remove conteúdo jurídico e segredos antes de logar/persistir."""
    clean: dict = {}
    for key, value in (meta or {}).items():
        lowered = str(key).lower()
        if any(marker in lowered for marker in _SENSITIVE_KEYS):
            continue
        if lowered in ("file_path", "path", "stack", "traceback"):
            continue
        clean[key] = value
    return clean


def record_dossier_event(
    *,
    logger_name: str,
    event: str,
    run_id: str | None = None,
    stage: str | None = None,
    metrics: dict | None = None,
    **extra,
) -> None:
    """Log estruturado do dossiê sem trecho, prompt, chave, path ou stack."""
    import logging as _logging

    payload = {"event": event, "run_id": run_id, "stage": stage}
    payload.update(sanitize_meta(metrics))
    payload.update(sanitize_meta(extra))
    _logging.getLogger(logger_name).info("dossier %s", payload)


def dossier_metrics(artifact, *, duration_s: float | None = None) -> dict:
    """Métricas por artefato: páginas, blocos, imagens, fontes e seções."""
    if hasattr(artifact, "model_dump"):
        content = artifact.model_dump(mode="json")
    else:
        content = getattr(artifact, "content", None) or artifact
    if not isinstance(content, dict):
        content = {}
    coverage = content.get("coverage", {}) or {}
    states = content.get("section_states", {}) or {}
    return {
        "pages_total": int(coverage.get("pages_total", 0) or 0),
        "pages_extracted": int(coverage.get("pages_extracted", 0) or 0),
        "unprocessed_blocks": len(coverage.get("unprocessed_block_ids", []) or []),
        "claims_found": len(content.get("claims", []) or []),
        "facts_found": len(content.get("facts", []) or []),
        "sources_found": len(content.get("sources", []) or []),
        "visuals_found": len(content.get("visuals", []) or []),
        "duration_s": duration_s,
        "status": getattr(artifact, "status", content.get("status")),
        "section_statuses": {
            section: (state.get("status") if isinstance(state, dict) else state)
            for section, state in states.items()
        },
    }


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
