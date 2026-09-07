import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import rag_answer
from app.core.embeddings import embed_query
from app.core.retrieval import hybrid_search
from app.crud.document import get_document_for_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def _resolve_scope(
    db: Session, *, current_user: User, document_id: str | None
) -> UUID | None:
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
        db, id=identifier, user_id=current_user.id
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return document.id


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
    scope = _resolve_scope(db, current_user=current_user, document_id=payload.document_id)
    try:
        result = rag_answer.answer_query(
            db,
            user_id=current_user.id,
            query=payload.query,
            document_id=scope,
            top_k=payload.top_k,
        )
    except Exception as exc:
        logger.exception("Falha no chat para %s: %s", current_user.id, exc)
        raise HTTPException(status_code=502, detail="Falha ao gerar resposta")
    return result


@router.post("/chat/stream")
def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    _require_ai()
    scope = _resolve_scope(db, current_user=current_user, document_id=payload.document_id)

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

    def event_stream():
        if not chunks:
            yield _sse(
                {
                    "token": "Nao encontrei fundamento nos seus documentos para responder a essa pergunta."
                }
            )
            yield _sse({"done": True, "citations": []})
            return
        contexts = [(str(c.id), c.content) for c in chunks]
        prompt = rag_answer.build_grounded_prompt(payload.query, contexts)
        try:
            for token, _model in rag_answer.complete_stream(prompt):
                yield _sse({"token": token})
        except Exception as exc:
            logger.exception("Falha no streaming para %s: %s", current_user.id, exc)
            yield _sse({"error": "Falha ao gerar resposta"})
            return
        yield _sse({"done": True, "citations": citations})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
