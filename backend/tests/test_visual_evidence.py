"""Onda 0 Task 7 — imagens como evidência (contrato visual)."""

import pytest

from app.core.visual_evidence import (
    VisualAccessDenied,
    build_visual_evidence,
    figures_state,
    normalize_region,
    resolve_visual_url,
)


def _figure(**overrides):
    base = {
        "id": "fig-1",
        "document_id": "doc-1",
        "revision_id": "rev-1",
        "user_id": "user-1",
        "page_number": 3,
        "bbox": {"l": 59.5, "t": 119, "r": 357, "b": 476},
        "kind": "photo",
        "caption": None,
        "file_path": "/tmp/fig-1.png",
        "sensitivity": [],
    }
    base.update(overrides)
    return base


def test_normalized_bbox_respects_rotation():
    region = normalize_region(
        bbox={"l": 59.5, "t": 119, "r": 357, "b": 476},
        page_width=595.0,
        page_height=842.0,
        rotation=90,
    )
    for key in ("x", "y", "width", "height"):
        assert 0.0 <= region[key] <= 1.0
    assert region["width"] > 0 and region["height"] > 0


def test_figure_keeps_document_revision_page_and_source():
    visuals = build_visual_evidence(
        figures=[_figure(block_id="b1")],
        blocks=[{"id": "b1"}],
        links={"b1": "src-1"},
    )
    assert len(visuals) == 1
    assert visuals[0]["document_id"] == "doc-1"
    assert visuals[0]["revision_id"] == "rev-1"
    assert visuals[0]["page_number"] == 3
    assert visuals[0]["source_ref"] == "src-1"


def test_caption_outside_crop_requires_page_context():
    visuals = build_visual_evidence(
        figures=[_figure(caption="legenda externa ao recorte")],
        blocks=[],
        links={},
    )
    assert visuals[0]["requires_page_context"] is True


def test_empty_list_with_image_blocks_is_extraction_failed():
    assert figures_state([], has_image_blocks=True) == "extraction_failed"
    assert figures_state([], has_image_blocks=False) == "ok_empty"


def test_sensitive_visual_starts_hidden():
    visuals = build_visual_evidence(
        figures=[_figure(sensitivity=["personal_data"])],
        blocks=[],
        links={},
    )
    assert visuals[0]["hidden_by_default"] is True


def test_other_users_document_cannot_resolve_thumbnail_or_page():
    figure = _figure(user_id="user-1")
    with pytest.raises(VisualAccessDenied):
        resolve_visual_url(figure=figure, requesting_user_id="user-2", kind="thumbnail")
    with pytest.raises(VisualAccessDenied):
        resolve_visual_url(figure=figure, requesting_user_id="user-2", kind="page")
    assert resolve_visual_url(figure=figure, requesting_user_id="user-1", kind="thumbnail")
