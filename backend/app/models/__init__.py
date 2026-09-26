from app.core.database import Base

# Model imports to make Alembic aware of them
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_figure import DocumentFigure
from app.models.document_revision import DocumentRevision
from app.models.analysis import Analysis
from app.models.analysis_artifact import AnalysisArtifact
from app.models.analysis_run import AnalysisRun
from app.models.template import Template
from app.models.generated_document import GeneratedDocument
from app.models.prompt_profile import PromptProfile
from app.models.audit_event import AuditEvent
from app.models.review_event import ReviewEvent
from app.models.source_block import SourceBlock
from app.models.source_reference import SourceReference
