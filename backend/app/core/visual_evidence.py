"""Evidência visual V3 (Onda 0 Task 7, §7).

Converte ``DocumentFigure`` em ``VisualEvidence`` sem duplicar catálogo:
chaves opacas de storage, nunca caminho absoluto no payload. Falha de
extração vira ``extraction_failed`` — nunca "documento sem imagens".
"""

from __future__ import annotations


class VisualAccessDenied(Exception):
    """Resolução negada: figura pertence a outro usuário."""

    code = "VISUAL_ACCESS_DENIED"


def normalize_region(
    *,
    bbox: dict | None,
    page_width: float,
    page_height: float,
    rotation: int = 0,
) -> dict:
    """Bbox absoluta → região normalizada 0-1 (rotação explícita).

    Para 90/270 a página é lida rotacionada; as coordenadas do extrator
    já vêm no espaço da página exibida, então normaliza contra as
    dimensões informadas e fixa valores em [0, 1].
    """
    if not bbox or not page_width or not page_height:
        return {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}
    rotation = int(rotation or 0) % 360
    l = float(bbox.get("l", bbox.get("x0", 0.0)) or 0.0)
    t = float(bbox.get("t", bbox.get("y0", 0.0)) or 0.0)
    r = float(bbox.get("r", bbox.get("x1", page_width)) or page_width)
    b = float(bbox.get("b", bbox.get("y1", page_height)) or page_height)

    def clamp(v: float) -> float:
        return max(0.0, min(1.0, v))

    x = clamp(min(l, r) / page_width)
    y = clamp(min(t, b) / page_height)
    w = clamp(abs(r - l) / page_width)
    h = clamp(abs(t - b) / page_height)
    return {"x": round(x, 4), "y": round(y, 4), "width": round(w, 4), "height": round(h, 4)}


def figures_state(figures: list | None, *, has_image_blocks: bool = False) -> str:
    """Estado honesto da extração visual (nunca mente ausência)."""
    if figures:
        return "ok_found"
    if has_image_blocks:
        return "extraction_failed"
    return "ok_empty"


def _opaque_key(figure: dict, suffix: str) -> str:
    fid = str(figure.get("id") or "fig")
    return f"visual-{fid}-{suffix}"


def build_visual_evidence(
    *,
    figures: list[dict],
    blocks: list[dict] | None = None,
    links: dict | None = None,
) -> list[dict]:
    """Converte figuras em evidência visual ligada a fontes e fatos."""
    links = links or {}
    visuals: list[dict] = []
    for figure in figures or []:
        fid = str(figure.get("id") or "")
        block_id = figure.get("block_id")
        source_ref = links.get(block_id) if block_id else None
        if source_ref is None and blocks:
            source_ref = links.get("default")
        sensitivity = list(figure.get("sensitivity") or [])
        caption = figure.get("caption")
        visuals.append(
            {
                "id": fid,
                "document_id": str(figure.get("document_id") or ""),
                "revision_id": str(figure.get("revision_id") or ""),
                "page_number": int(figure.get("page_number") or 1),
                "kind": figure.get("kind") or "other",
                "status": figure.get("status") or "examined",
                "storage_key": figure.get("storage_key") or _opaque_key(figure, "bin"),
                "thumbnail_key": figure.get("thumbnail_key") or _opaque_key(figure, "thumb"),
                "caption_original": caption,
                "requires_page_context": bool(caption),
                "sensitivity": sensitivity,
                "hidden_by_default": bool(sensitivity),
                "related_fact_ids": list(figure.get("related_fact_ids") or []),
                "related_claim_ids": list(figure.get("related_claim_ids") or []),
                "related_evidence_ids": list(figure.get("related_evidence_ids") or []),
                "source_ref": source_ref or "",
            }
        )
    return visuals


def resolve_visual_url(*, figure: dict, requesting_user_id: str, kind: str = "thumbnail") -> str:
    """URL opaca de miniatura/página com checagem de dono."""
    if str(figure.get("user_id") or "") != str(requesting_user_id):
        raise VisualAccessDenied("figura pertence a outro usuário")
    fid = str(figure.get("id") or "fig")
    return f"visual://{fid}/{kind}"
