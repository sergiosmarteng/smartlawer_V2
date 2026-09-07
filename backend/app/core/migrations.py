import logging
from functools import lru_cache
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.core.config import settings
from app.core.database import Base, engine
from app.models import Analysis, Document, DocumentChunk, Template, User  # noqa: F401

logger = logging.getLogger(__name__)

REQUIRED_TABLES = {"users", "documents", "analyses", "templates", "document_chunks"}


@lru_cache(maxsize=1)
def _get_alembic_config() -> Config:
    project_root = Path(__file__).resolve().parents[2]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return config


def _repair_missing_tables() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    missing_tables = REQUIRED_TABLES - existing_tables
    if not missing_tables:
        return

    logger.warning(
        "Database schema is incomplete; recreating missing tables: %s",
        ", ".join(sorted(missing_tables)),
    )
    Base.metadata.create_all(bind=engine)


def run_migrations() -> None:
    logger.info("Applying database migrations")
    command.upgrade(_get_alembic_config(), "head")
    _repair_missing_tables()
