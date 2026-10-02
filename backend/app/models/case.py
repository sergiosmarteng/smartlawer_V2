"""Caso jurídico (Onda 0 Task 2, spec universal §10.1).

Um ``Case`` agrupa documentos de um mesmo assunto jurídico. O snapshot da
execução guarda ``case_id`` para reanálise preservando o agrupamento.
``CaseDocument`` associa um ``Document`` a um caso com um papel material
(``petição``, ``contestação``, ``documento novo``, ``prova``, ...).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (
        Index("ix_cases_user", "user_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=True)
    area = Column(String(60), nullable=True)  # área principal detectada (best-effort)
    description = Column(String(2000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    user = relationship("User")
    documents = relationship(
        "CaseDocument",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    runs = relationship("AnalysisRun", back_populates="case")


class CaseDocument(Base):
    __tablename__ = "case_documents"
    __table_args__ = (
        Index("ix_case_documents_case", "case_id"),
        Index("ix_case_documents_document", "document_id"),
        UniqueConstraint("case_id", "document_id", name="uq_case_documents_case_document"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(60), nullable=False, default="documento")
    added_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    case = relationship("Case", back_populates="documents")
    document = relationship("Document")