import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import rag_answer
from app.core.audit import record_audit
from app.core.embeddings import embed_query
from app.core.retrieval import hybrid_search
from app.core.security_rag import BLOCK_MESSAGE, is_injection_attempt, mask_pii
from app.crud.document import get_document_for_user
from app.models.audit_event import AuditEvent
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def _resolve_scope(
    db: Session, *, current_user: User, document_id: str | None
):
    """Validate and return the scoped Document (with analysis) or None."""
    if document_id is None:
        return None
    try:
        identifier = UUID(str(document_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="document_id inválido",
        )
    document = get_document_for_user(
        db, id=identifier, user_id=current_user.id, load_analysis=True
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return document


def _require_ai() -> None:
    if not rag_answer.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Chat indisponível: chave de IA não configurada",
        )


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    _require_ai()
    scoped_document = _resolve_scope(
        db, current_user=current_user, document_id=payload.document_id
    )
    scope = scoped_document.id if scoped_document is not None else None
    try:
        result = rag_answer.answer_query(
            db,
            user_id=current_user.id,
            query=payload.query,
            document_id=scope,
            top_k=payload.top_k,
        )
    except Exception as exc:
        logger.exception("Falha no chat para user_id=%s", current_user.id)
        raise HTTPException(status_code=502, detail="Falha ao gerar resposta")
    # Audit stores counts/scope only — never the raw query (LGPD).
    if isinstance(result, dict):
        audit_model = result.get("model")
        audit_citations = len(result.get("citations") or [])
    else:
        audit_model = getattr(result, "model", None)
        audit_citations = len(getattr(result, "citations", None) or [])
    record_audit(
        db,
        event_type=AuditEvent.CHAT_QUERY,
        user_id=current_user.id,
        entity_type="document" if scope else None,
        entity_id=scope,
        meta={"model": audit_model, "citations": audit_citations},
    )
    return result


@router.post("/chat/stream")
def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    _require_ai()
    scoped_document = _resolve_scope(
        db, current_user=current_user, document_id=payload.document_id
    )
    scope = scoped_document.id if scoped_document is not None else None

    if is_injection_attempt(payload.query):
        logger.warning(
            "Chat stream bloqueado (injection): %s", mask_pii(payload.query, max_len=200)
        )

        def blocked_stream():
            yield _sse({"token": BLOCK_MESSAGE})
            yield _sse(
                {
                    "done": True,
                    "citations": [],
                    "suggested_questions": [],
                    "ai_draft": True,
                    "requires_human_review": True,
                }
            )

        return StreamingResponse(blocked_stream(), media_type="text/event-stream")

    embedding = embed_query(payload.query)
    chunks = hybrid_search(
        db,
        user_id=current_user.id,
        query_text=payload.query,
        query_embedding=embedding,
        top_k=payload.top_k,
        document_id=scope,
    )
    citations = rag_answer._to_citations(chunks)
    case_brief = ""
    if scoped_document is not None and scoped_document.analysis is not None:
        case_brief = rag_answer.build_case_brief(
            scoped_document.filename, scoped_document.analysis
        )
        citations.append(
            rag_answer.analysis_citation(
                scoped_document.id, scoped_document.filename, scoped_document.analysis
            )
        )

    def event_stream():
        if not chunks and not case_brief:
            yield _sse({"token": rag_answer.FALLBACK_NO_BASIS})
            yield _sse(
                {
                    "done": True,
                    "citations": [],
                    "suggested_questions": [],
                    "ai_draft": True,
                    "requires_human_review": True,
                }
            )
            return
        contexts = [(str(c.id), c.content) for c in chunks]
        prompt = rag_answer.build_counsel_prompt(payload.query, contexts, case_brief)
        full_text = ""
        try:
            for token, _model in rag_answer.complete_stream(
                prompt, system=rag_answer.COUNSEL_SYSTEM_PROMPT
            ):
                full_text += token
                yield _sse({"token": token})
        except Exception as exc:
            logger.exception("Falha no streaming para user_id=%s", current_user.id)
            yield _sse({"error": "Falha ao gerar resposta"})
            yield _sse(
                {
                    "done": True,
                    "citations": citations,
                    "suggested_questions": [],
                    "ai_draft": True,
                    "requires_human_review": True,
                }
            )
            return
        try:
            suggestions = rag_answer.suggest_followups(payload.query, full_text)
        except Exception:
            logger.exception("Falha ao gerar follow-ups no stream para user_id=%s", current_user.id)
            suggestions = []
        yield _sse(
            {
                "done": True,
                "citations": citations,
                "suggested_questions": suggestions,
                "ai_draft": True,
                "requires_human_review": True,
            }
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
