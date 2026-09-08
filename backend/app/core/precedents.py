"""Curated jurisprudence corpus as shared RAG source (C5/BL-023).

Design: precedents live as ordinary ``document_chunks`` owned by a fixed
system user (one system Document per precedent, so citations resolve to
``[Jurisprudência] TRIBUNAL número — tema`` labels). Retrieval includes
the system user alongside the caller (closed two-id allowlist), so the
tenant barrier stays intact. No new tables, no migration.

Seed content is thesis-level paraphrase of famous holdings with official
source portals — counsel should review before production reliance.
"""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_USER_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "smartlawer.system-user")
SYSTEM_MATTER_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "smartlawer.precedents")
SYSTEM_USER_EMAIL = "sistema@smartlawer.local"
SYSTEM_USER_NAME = "sistema"
CORPUS_VERSION = "v1"
NOOP_EMBEDDING_MODEL = "seed-noop"

PRECEDENTS: list[dict] = [
    {
        "key": "stf-sv-11",
        "tribunal": "STF",
        "numero": "Súmula Vinculante 11",
        "tema": "Uso de algemas",
        "tese": (
            "O uso de algemas só é lícito em caso de resistência e de fundado "
            "receio de fuga ou de perigo à integridade física própria ou alheia, "
            "devendo a excepcionalidade ser justificada por escrito, sob pena de "
            "nulidade e responsabilidade do agente e do Estado."
        ),
        "fonte": "Portal de jurisprudência do STF",
    },
    {
        "key": "stf-sv-13",
        "tribunal": "STF",
        "numero": "Súmula Vinculante 13",
        "tema": "Nepotismo",
        "tese": (
            "É vedada a nomeação de cônjuge, companheiro ou parente em linha reta, "
            "colateral ou por afinidade até o terceiro grau para cargos em comissão "
            "ou de confiança, de direção, chefia ou assessoramento, na administração "
            "pública direta e indireta."
        ),
        "fonte": "Portal de jurisprudência do STF",
    },
    {
        "key": "stf-sv-10",
        "tribunal": "STF",
        "numero": "Súmula Vinculante 10",
        "tema": "Reserva de plenário",
        "tese": (
            "Órgão fracionário de tribunal não pode afastar a incidência de lei, "
            "ainda que sem declará-la expressamente inconstitucional, salvo se já "
            "houver manifestação do plenário do próprio tribunal ou do STF sobre "
            "a matéria (reserva de plenário, art. 97 da Constituição)."
        ),
        "fonte": "Portal de jurisprudência do STF",
    },
    {
        "key": "stj-sum-297",
        "tribunal": "STJ",
        "numero": "Súmula 297",
        "tema": "CDC e instituições financeiras",
        "tese": (
            "O Código de Defesa do Consumidor aplica-se às instituições "
            "financeiras, alcançando os contratos bancários e a prestação de "
            "serviços no mercado de consumo."
        ),
        "fonte": "Súmulas do STJ",
    },
    {
        "key": "stj-sum-479",
        "tribunal": "STJ",
        "numero": "Súmula 479",
        "tema": "Fraudes bancárias e fortuito interno",
        "tese": (
            "As instituições financeiras respondem objetivamente pelos danos "
            "gerados por fortuito interno relativo a fraudes e delitos praticados "
            "por terceiros no âmbito de operações bancárias."
        ),
        "fonte": "Súmulas do STJ",
    },
    {
        "key": "stf-tema-69",
        "tribunal": "STF",
        "numero": "Tema 69 da repercussão geral (RE 574.706)",
        "tema": "ICMS na base do PIS e da COFINS",
        "tese": (
            "O ICMS não compõe a base de cálculo para fins de incidência do PIS "
            "e da COFINS (tese do século), por não se incorporar ao patrimônio "
            "do contribuinte."
        ),
        "fonte": "Portal de jurisprudência do STF",
    },
]


def precedent_label(item: dict) -> str:
    return f"[Jurisprudência] {item['tribunal']} {item['numero']} — {item['tema']}"


def precedent_content(item: dict) -> str:
    return (
        f"{item['tribunal']} — {item['numero']} ({item['tema']}). "
        f"Tese: {item['tese']} Fonte: {item['fonte']}."
    )


def _expected_version() -> str:
    return f"seed:{CORPUS_VERSION}:{settings.EMBEDDING_MODEL}"


def _keys_available() -> bool:
    return bool(settings.OPENAI_API_KEY or settings.OPENROUTER_API_KEY)


def _seed_state(db: Session) -> tuple[str | None, str | None, int]:
    """(embedding_model, embedding_model_version, row count) of the corpus."""
    from app.models.document_chunk import DocumentChunk

    row = (
        db.query(
            DocumentChunk.embedding_model, DocumentChunk.embedding_model_version
        )
        .filter(DocumentChunk.matter_id == SYSTEM_MATTER_ID)
        .first()
    )
    count = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.matter_id == SYSTEM_MATTER_ID)
        .count()
    )
    if row is None:
        return None, None, 0
    return row[0], row[1], count


def ensure_precedents(db: Session, *, embed_fn=None) -> dict:
    """Seed the shared jurisprudence corpus idempotently.

    Reseeds when the corpus version or the effective embedding model
    changes (e.g. API keys configured after a keyless seed). Returns a
    status dict. Never raises — seeding must not break boot or requests.
    """
    from app.models.document import Document
    from app.models.document_chunk import DocumentChunk
    from app.models.user import User

    try:
        model, version, count = _seed_state(db)
        if (
            version == _expected_version()
            and count == len(PRECEDENTS)
            and (model != NOOP_EMBEDDING_MODEL or not _keys_available())
        ):
            return {"status": "up-to-date", "count": count}

        # (Re)seed: replace the whole system corpus atomically-ish.
        db.query(DocumentChunk).filter(
            DocumentChunk.matter_id == SYSTEM_MATTER_ID
        ).delete()
        db.query(Document).filter(
            Document.user_id == SYSTEM_USER_ID,
            Document.file_path.like("precedents://%"),
        ).delete()

        system_user = db.query(User).filter(User.id == SYSTEM_USER_ID).first()
        if system_user is None:
            system_user = User(
                id=SYSTEM_USER_ID,
                email=SYSTEM_USER_EMAIL,
                username=SYSTEM_USER_NAME,
                hashed_password="!",
                is_active=False,
            )
            db.add(system_user)
            db.flush()

        texts = [precedent_content(item) for item in PRECEDENTS]
        vectors: list | None = None
        if embed_fn is not None:
            try:
                vectors = embed_fn(texts)
            except Exception as exc:
                logger.warning("Precedent embedding fn failed (%s); using noop.", exc)
                vectors = None
        if not vectors:
            try:
                from app.core.embeddings import embed_texts

                vectors = embed_texts(texts) or None
            except Exception as exc:
                logger.warning("Precedent embeddings unavailable (%s).", exc)
                vectors = None

        use_real_vectors = bool(vectors) and len(vectors) == len(texts)
        marker = _expected_version()
        zero_vector = [0.0] * settings.EMBEDDING_DIMENSIONS

        now = datetime.now(timezone.utc)
        for index, item in enumerate(PRECEDENTS):
            document = Document(
                user_id=SYSTEM_USER_ID,
                filename=precedent_label(item)[:255],
                file_path=f"precedents://{CORPUS_VERSION}/{item['key']}",
                content_type="text/plain",
                status=Document.STATUS_COMPLETED,
                status_detail="Curadoria de jurisprudência (sistema)",
                uploaded_at=now,
                completed_at=now,
            )
            db.add(document)
            db.flush()
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    user_id=SYSTEM_USER_ID,
                    matter_id=SYSTEM_MATTER_ID,
                    chunk_index=0,
                    content=texts[index],
                    token_count=len(texts[index].split()),
                    embedding=list(vectors[index]) if use_real_vectors else list(zero_vector),
                    embedding_model=(
                        settings.EMBEDDING_MODEL if use_real_vectors else NOOP_EMBEDDING_MODEL
                    ),
                    embedding_model_version=marker,
                )
            )
        db.commit()
        return {
            "status": "seeded",
            "count": len(PRECEDENTS),
            "vectors": "real" if use_real_vectors else "noop",
        }
    except Exception as exc:
        logger.warning("Precedent seeding failed (%s).", exc)
        try:
            db.rollback()
        except Exception:
            pass
        return {"status": "failed", "error": str(exc)[:200]}
