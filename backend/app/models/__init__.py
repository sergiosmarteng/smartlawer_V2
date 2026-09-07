from app.core.database import Base

# Model imports to make Alembic aware of them
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.analysis import Analysis
from app.models.template import Template
