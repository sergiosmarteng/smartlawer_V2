"""Docling-based PDF ingestion with safe fallback.

``extract_markdown`` converts a PDF into structured markdown. It NEVER
raises: when Docling is unavailable it returns ``None`` so the caller
falls back to :class:`PDFExtractor` raw text.

``extract_figures`` lists every picture/chart found in the PDF with
``page_number``, ``bbox``, ``caption`` and the crop saved under
*output_dir*. It NEVER raises: any failure yields ``[]``. Docling is
the primary source (``generate_picture_images=True``); when Docling is
missing, fails or finds nothing, a PyMuPDF (fitz) fallback extracts
embedded raster images so the pipeline still reports figures.
"""

import logging
import os

logger = logging.getLogger(__name__)

MAX_FIGURES = 50

_converter = None


def _get_converter():
    """Lazily build and cache the Docling converter (singleton)."""
    global _converter
    if _converter is None:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import (
            DocumentConverter,
            PdfFormatOption,
        )

        pipeline = PdfPipelineOptions()
        pipeline.generate_picture_images = True
        pipeline.images_scale = 2.0
        _converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline)
            }
        )
    return _converter


def extract_markdown(file_path: str) -> str | None:
    """Convert *file_path* PDF to markdown, or ``None`` on any failure."""
    try:
        converter = _get_converter()
    except ImportError:
        logger.warning("Docling is not installed; skipping markdown ingestion.")
        return None
    except Exception as exc:
        logger.warning("Docling converter init failed (%s); skipping.", exc)
        return None

    try:
        result = converter.convert(file_path)
        markdown = result.document.export_to_markdown()
    except Exception as exc:
        logger.warning("Docling conversion failed for %s (%s); skipping.", file_path, exc)
        return None

    if not markdown or not markdown.strip():
        logger.warning("Docling returned empty markdown for %s; skipping.", file_path)
        return None
    return markdown.strip()


def extract_figures(file_path: str, output_dir: str) -> list[dict]:
    """Extract pictures/charts from *file_path* into *output_dir*.

    Returns a list of ``{page_number, bbox, caption, file_path,
    content_type}``. Never raises: failures yield ``[]``. Tries Docling
    first, then PyMuPDF fallback when Docling finds nothing.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as exc:
        logger.warning("Cannot create figures dir %s (%s).", output_dir, exc)
        return []

    figures = _extract_figures_docling(file_path, output_dir)
    if figures:
        logger.info("Docling extraiu %d figura(s) de %s.", len(figures), file_path)
        return figures[:MAX_FIGURES]

    fallback = _extract_figures_fitz(file_path, output_dir)
    if fallback:
        logger.info("Fallback fitz extraiu %d figura(s) de %s.", len(fallback), file_path)
    else:
        logger.info("Nenhuma figura encontrada em %s.", file_path)
    return fallback[:MAX_FIGURES]


def _extract_figures_docling(file_path: str, output_dir: str) -> list[dict]:
    try:
        converter = _get_converter()
    except Exception as exc:
        logger.warning("Docling indisponível para figuras (%s); usando fallback.", exc)
        return []
    try:
        result = converter.convert(file_path)
        doc = result.document
    except Exception as exc:
        logger.warning("Docling falhou nas figuras de %s (%s).", file_path, exc)
        return []

    try:
        from docling_core.types.doc import DocItemLabel
    except Exception as exc:
        logger.warning("Docling labels indisponíveis (%s).", exc)
        return []

    figures: list[dict] = []
    try:
        items = list(doc.iterate_items())
    except Exception as exc:
        logger.warning("Docling iterate_items falhou (%s).", exc)
        return []

    index = 0
    for item, _level in items:
        label = getattr(item, "label", None)
        if label not in (DocItemLabel.PICTURE, DocItemLabel.CHART):
            continue
        index += 1
        if index > MAX_FIGURES:
            logger.warning("Limite de %d figuras atingido; truncando.", MAX_FIGURES)
            break
        page_number = None
        bbox = None
        try:
            prov = getattr(item, "prov", None) or []
            if prov:
                page_number = getattr(prov[0], "page_no", None)
                raw_bbox = getattr(prov[0], "bbox", None)
                if raw_bbox is not None:
                    bbox = {
                        "l": getattr(raw_bbox, "l", None),
                        "t": getattr(raw_bbox, "t", None),
                        "r": getattr(raw_bbox, "r", None),
                        "b": getattr(raw_bbox, "b", None),
                    }
        except Exception:
            pass
        caption = None
        try:
            captions = getattr(item, "captions", None) or []
            texts = [getattr(c, "text", "") for c in captions]
            texts = [t.strip() for t in texts if t and t.strip()]
            caption = " ".join(texts) or None
        except Exception:
            caption = None

        saved_path = None
        try:
            image = item.get_image(doc)
            if image is not None:
                saved_path = os.path.join(
                    output_dir, f"fig_{index:03d}_p{page_number or 0}.png"
                )
                image.save(saved_path, format="PNG")
        except Exception as exc:
            logger.warning("Falha ao salvar crop da figura %d (%s).", index, exc)
            saved_path = None

        figures.append(
            {
                "page_number": page_number,
                "bbox": bbox,
                "caption": caption,
                "file_path": saved_path,
                "content_type": "image/png",
            }
        )
    return figures


def _extract_figures_fitz(file_path: str, output_dir: str) -> list[dict]:
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as exc:
        logger.warning("Cannot create figures dir %s (%s).", output_dir, exc)
        return []
    try:
        import fitz
    except ImportError:
        logger.warning("fitz indisponível; sem fallback de figuras.")
        return []
    try:
        doc = fitz.open(file_path)
    except Exception as exc:
        logger.warning("fitz não abriu %s (%s).", file_path, exc)
        return []

    figures: list[dict] = []
    try:
        for page_number in range(len(doc)):
            try:
                images = doc.load_page(page_number).get_images(full=True)
            except Exception:
                continue
            for xref_tuple in images:
                if len(figures) >= MAX_FIGURES:
                    break
                try:
                    xref = xref_tuple[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha > 3:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    index = len(figures) + 1
                    saved_path = os.path.join(
                        output_dir, f"fig_{index:03d}_p{page_number + 1}.png"
                    )
                    pix.save(saved_path)
                    figures.append(
                        {
                            "page_number": page_number + 1,
                            "bbox": None,
                            "caption": None,
                            "file_path": saved_path,
                            "content_type": "image/png",
                        }
                    )
                except Exception:
                    continue
    finally:
        try:
            doc.close()
        except Exception:
            pass
    return figures


def reset_converter_cache() -> None:
    """Test hook: drop the cached converter."""
    global _converter
    _converter = None
