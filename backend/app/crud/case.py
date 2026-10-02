"""CRUD de casos jurídicos (Onda 0 Task 2).

Autorização estrita: ``attach_document`` rejeita documento de outro
usuário. Nenhuma mutação reescreve o snapshot do ``AnalysisRun`` — esse é
o invariante preservado por ``test_substituting_file_after_snapshot_keeps_revision_ids``.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.case import Case, CaseDocument
from app.models.document import Document


class CaseAccessError(Exception):
    """Operação negada: documento não pertence ao dono do caso."""

    code = "CASE_ACCESS_DENIED"


def create_case(
    db: Session,
    *,
    user_id: UUID | str,
    name: str | None = None,
    area: str | None = None,
    description: str | None = None,
) -> Case:
    """Cria um novo caso para o usuário."""
    case = Case(
        user_id=user_id,
        name=name,
        area=area,
        description=description,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, *, case_id: UUID | str) -> Case | None:
    return db.query(Case).filter(Case.id == case_id).one_or_none()


def attach_document(
    db: Session,
    *,
    case: Case,
    document: Document,
    role: str = "documento",
) -> CaseDocument:
    """Anexa um documento ao caso, rejeitando documentos alheios."""
    if str(document.user_id) != str(case.user_id):
        raise CaseAccessError(
            f"documento {document.id} não pertence ao usuário do caso {case.id}"
        )

    existing = (
        db.query(CaseDocument)
        .filter(
            CaseDocument.case_id == case.id,
            CaseDocument.document_id == document.id,
        )
        .one_or_none()
    )
    if existing is not None:
        return existing

    link = CaseDocument(
        case_id=case.id,
        document_id=document.id,
        role=role,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link