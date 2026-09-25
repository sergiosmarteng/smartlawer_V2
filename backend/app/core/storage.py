"""Caminhos de armazenamento compartilhados (upload + figuras)."""

import os

UPLOAD_DIRECTORY = (
    "/data/uploads"
    if os.environ.get("ENVIRONMENT") != "development_local"
    else "./uploads"
)


def upload_directory() -> str:
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
    return UPLOAD_DIRECTORY


def figure_directory(document_id: str) -> str:
    path = os.path.join(upload_directory(), "figures", str(document_id))
    os.makedirs(path, exist_ok=True)
    return path
