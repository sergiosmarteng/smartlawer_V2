"""Contrato único de extração por página/bloco (V2 T03, §6).

Unifica PyMuPDF e Docling num inventário verificável: cada página tem
número físico, dimensões, rotação, método e blocos; cada bloco tem ID
estável na revisão, tipo, ordem de leitura, bbox normalizada e hash.
Cabeçalhos/rodapés repetidos são marcados como ruído de navegação
(sem destruir o original). OCR é decidido por cobertura espacial, não
só por contagem de caracteres (D07).
"""

import hashlib
import logging
import re

logger = logging.getLogger(__name__)

# Fração da área da página coberta por imagens para suspeitar de corpo
# digitalizado mesmo com cabeçalho textual legível (D07).
HYBRID_IMAGE_AREA_RATIO = 0.40
HYBRID_MIN_TEXT_CHARS = 500
OCR_MIN_TEXT_CHARS = 50

BLOCK_TEXT = "text"
BLOCK_HEADING = "heading"
BLOCK_TABLE = "table"
BLOCK_IMAGE = "image"
BLOCK_HEADER = "header"
BLOCK_FOOTER = "footer"

FLAG_NAVIGATION_NOISE = "navigation_noise"
FLAG_SCANNED_BODY = "scanned_body"
FLAG_HYBRID_PAGE = "hybrid_page"
FLAG_BLANK = "blank"
FLAG_TRUNCATED_FIGURES = "truncated_figures"

FIGURES_OK_FOUND = "ok_found"
FIGURES_OK_EMPTY = "ok_empty"
FIGURES_FAILED = "failed"
FIGURES_TRUNCATED = "truncated"


def normalize_block_text(text: str) -> str:
    """Normaliza sem destruir o original: desfaz hifenização de quebra
    de linha, colapsa espaços e preserva o texto para offset de citação."""
    text = (text or "").replace("\x00", "")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def stable_block_id(revision_id: str, page_number: int, index: int, text: str) -> str:
    seed = f"{revision_id}:{page_number}:{index}:{text or ''}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def _normalize_bbox(bbox: dict | tuple | list | None, width: float, height: float) -> dict | None:
    try:
        if bbox is None:
            return None
        if isinstance(bbox, dict):
            l, t, r, b = bbox["l"], bbox["t"], bbox["r"], bbox["b"]
        else:
            l, t, r, b = bbox[0], bbox[1], bbox[2], bbox[3]
        if not width or not height:
            return None
        return {
            "x0": round(float(l) / width, 4),
            "y0": round(float(t) / height, 4),
            "x1": round(float(r) / width, 4),
            "y1": round(float(b) / height, 4),
        }
    except Exception:
        return None


def build_pages_from_fitz(file_path: str, revision_id: str) -> list[dict]:
    """Inventário de páginas/blocos via PyMuPDF (adapter; pode levantar)."""
    import fitz

    doc = fitz.open(file_path)
    try:
        pages: list[dict] = []
        for page_number in range(len(doc)):
            page = doc.load_page(page_number)
            rect = page.rect
            width, height = float(rect.width), float(rect.height)
            rotation = int(getattr(page, "rotation", 0) or 0)
            raw = page.get_text("dict")
            blocks: list[dict] = []
            for index, raw_block in enumerate(raw.get("blocks", [])):
                if raw_block.get("type") == 1:
                    blocks.append(
                        {
                            "id": stable_block_id(revision_id, page_number + 1, index, ""),
                            "type": BLOCK_IMAGE,
                            "reading_order": index,
                            "bbox": _normalize_bbox(raw_block.get("bbox"), width, height),
                            "original_text": "",
                            "normalized_text": "",
                            "quality_flags": [],
                        }
                    )
                    continue
                lines = []
                for line in raw_block.get("lines", []):
                    for span in line.get("spans", []):
                        lines.append(span.get("text", ""))
                original = "\n".join(lines)
                blocks.append(
                    {
                        "id": stable_block_id(revision_id, page_number + 1, index, original),
                        "type": BLOCK_TEXT,
                        "reading_order": index,
                        "bbox": _normalize_bbox(raw_block.get("bbox"), width, height),
                        "original_text": original,
                        "normalized_text": normalize_block_text(original),
                        "quality_flags": [],
                    }
                )
            image_rects: list = []
            try:
                for xref_tuple in page.get_images(full=True):
                    try:
                        image_rects.extend(page.get_image_rects(xref_tuple[0]))
                    except Exception:
                        continue
                image_area = sum(max(0.0, r.width * r.height) for r in image_rects)
            except Exception:
                image_area = 0.0
            page_area = (width * height) or 1.0
            pages.append(
                {
                    "page_number": page_number + 1,
                    "width": width,
                    "height": height,
                    "rotation": rotation,
                    "method": "pymupdf",
                    "blocks": blocks,
                    "image_count": len(image_rects),
                    "image_area_ratio": round(image_area / page_area, 4),
                    "quality_flags": [],
                }
            )
        return pages
    finally:
        try:
            doc.close()
        except Exception:
            pass


def mark_navigation_noise(pages: list[dict], *, min_pages: int = 3) -> list[dict]:
    """Marca como ruído o texto curto repetido no topo/rodapé (D07).

    Só marca blocos de até 300 chars idênticos (normalizados) que abrem
    ou fecham ``min_pages`` ou mais páginas. O original é preservado.
    """
    from collections import Counter

    edge_texts: Counter[str] = Counter()
    for page in pages:
        blocks = page.get("blocks", [])
        edges = (blocks[:1] + blocks[-1:]) if blocks else []
        for block in edges:
            text = normalize_block_text(block.get("original_text", ""))
            if text and len(text) <= 300:
                edge_texts[text] += 1
    repeated = {t for t, n in edge_texts.items() if n >= min_pages}
    for page in pages:
        blocks = page.get("blocks", [])
        if not blocks:
            continue
        edges = [(blocks[0], BLOCK_HEADER)]
        if len(blocks) > 1:
            edges.append((blocks[-1], BLOCK_FOOTER))
        for block, edge_type in edges:
            text = normalize_block_text(block.get("original_text", ""))
            if text in repeated and block.get("type") == BLOCK_TEXT:
                block["type"] = edge_type
                flags = block.setdefault("quality_flags", [])
                if FLAG_NAVIGATION_NOISE not in flags:
                    flags.append(FLAG_NAVIGATION_NOISE)
    return pages


def assess_page_quality(page: dict) -> dict:
    """Diagnóstico por página: OCR por cobertura espacial (D07)."""
    text_chars = sum(
        len(b.get("normalized_text", ""))
        for b in page.get("blocks", [])
        if b.get("type") in (BLOCK_TEXT, BLOCK_HEADING, BLOCK_TABLE)
    )
    image_ratio = page.get("image_area_ratio", 0.0) or 0.0
    flags: list[str] = []
    if text_chars == 0:
        flags.append(FLAG_BLANK if image_ratio == 0 else FLAG_SCANNED_BODY)
    elif text_chars < OCR_MIN_TEXT_CHARS:
        flags.append(FLAG_SCANNED_BODY)
    elif image_ratio >= HYBRID_IMAGE_AREA_RATIO and text_chars < HYBRID_MIN_TEXT_CHARS:
        flags.append(FLAG_HYBRID_PAGE)
    page["text_chars"] = text_chars
    page["quality_flags"] = sorted(set(page.get("quality_flags", []) + flags))
    return page


def page_needs_ocr(page_or_text, image_area_ratio: float = 0.0) -> bool:
    """Decide OCR por cobertura: corpo digitalizado sob cabeçalho (D07)."""
    if isinstance(page_or_text, dict):
        assess_page_quality(page_or_text)
        flags = page_or_text.get("quality_flags", [])
        return FLAG_SCANNED_BODY in flags or FLAG_HYBRID_PAGE in flags
    text_chars = len((page_or_text or "").strip())
    if text_chars < OCR_MIN_TEXT_CHARS:
        return True
    return image_area_ratio >= HYBRID_IMAGE_AREA_RATIO and text_chars < HYBRID_MIN_TEXT_CHARS


def build_coverage(pages: list[dict]) -> dict:
    """Cobertura verificável §6.1: páginas, blocos e pendências."""
    issues = [p["page_number"] for p in pages if p.get("quality_flags")]
    noise = sum(
        1
        for p in pages
        for b in p.get("blocks", [])
        if FLAG_NAVIGATION_NOISE in b.get("quality_flags", [])
    )
    blocks_total = sum(len(p.get("blocks", [])) for p in pages)
    return {
        "pages_total": len(pages),
        "pages_extracted": len(pages),
        "pages_with_issues": issues,
        "blocks_total": blocks_total,
        "noise_blocks": noise,
    }


def text_without_noise(pages: list[dict]) -> str:
    """Texto para análise: exclui ruído de navegação (D03/D07)."""
    parts = []
    for page in pages:
        for block in page.get("blocks", []):
            if FLAG_NAVIGATION_NOISE in block.get("quality_flags", []):
                continue
            text = block.get("normalized_text", "")
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


def extract_inventory(file_path: str, revision_id: str) -> tuple[list[dict], dict]:
    """Pipeline do contrato: adapter → ruído → qualidade → cobertura.

    Nunca levanta: falha total retorna ([], {"extraction_error": ...}).
    """
    try:
        pages = build_pages_from_fitz(file_path, revision_id)
    except Exception as exc:
        logger.warning("Inventário de extração falhou para %s (%s).", file_path, exc)
        return [], {"extraction_error": str(exc), "pages_total": 0}
    mark_navigation_noise(pages)
    for page in pages:
        assess_page_quality(page)
    return pages, build_coverage(pages)


def figures_with_state(
    figures: list[dict] | None, *, failed: bool = False, truncated: bool = False
) -> tuple[list[dict], str]:
    """Distingue ausência de imagens de falha de extração (V2 §6).

    Nunca mostrar “documento sem figuras” quando a extração falhou.
    """
    if failed or figures is None:
        return [], FIGURES_FAILED
    if truncated:
        return figures or [], FIGURES_TRUNCATED
    if not figures:
        return [], FIGURES_OK_EMPTY
    return figures, FIGURES_OK_FOUND
