"""Contrato de copy: todo status_detail do pipeline tem frase PT-BR (upload).

Espelha as famílias de regex de `describeProcessingStage` (upload.tsx).
Nova etapa no backend sem família correspondente quebra este teste de
propósito — atualize a copy junto.
"""

import re
from pathlib import Path

# Famílias espelhadas de STAGE_PHRASES (src/pages/upload.tsx).
FAMILIES = [
    re.compile(r"converting.*markdown|structured markdown", re.I),
    re.compile(r"extracting text", re.I),
    re.compile(r"figur|image|picture", re.I),
    re.compile(r"generating legal analysis", re.I),
    re.compile(r"chunk|embed|index", re.I),
    re.compile(r"extract", re.I),
    re.compile(r"analysis|fallback", re.I),
    re.compile(r"retry|retrying", re.I),
    re.compile(r"queue|upload|sending", re.I),
    re.compile(r"compos|report|docx|summary", re.I),
    re.compile(r"audit|complet|ready|final|failed|unavailable", re.I),
]

FALLBACK_OK = re.compile(r"processando documento", re.I)


def _pipeline_status_details() -> list[str]:
    source = Path(__file__).resolve().parents[1] / "app" / "tasks" / "document_tasks.py"
    text = source.read_text(encoding="utf-8")
    literals = re.findall(r'status_detail=(?:"([^"]+)"|f"([^"]+)")', text)
    return [a or b for a, b in literals]


def test_every_pipeline_stage_has_ptbr_family():
    details = _pipeline_status_details()
    assert details, "nenhum status_detail encontrado no pipeline"
    uncovered = [
        detail
        for detail in details
        if not any(family.search(detail) for family in FAMILIES)
    ]
    assert uncovered == [], f"etapas sem frase PT-BR: {uncovered}"


def test_fallback_phrase_is_defined():
    page = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "pages"
        / "upload.tsx"
    ).read_text(encoding="utf-8")
    assert "Processando documento…" in page
    assert "Converting PDF to structured markdown" not in page
    assert "animate-spin" in page
