import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import logging

from app.core.extraction import page_needs_ocr

logger = logging.getLogger(__name__)


def _image_area_ratio(page) -> float:
    """Fração da área da página coberta por imagens (D07)."""
    try:
        rect = page.rect
        page_area = float(rect.width * rect.height) or 1.0
        area = 0.0
        for xref_tuple in page.get_images(full=True):
            try:
                for image_rect in page.get_image_rects(xref_tuple[0]):
                    area += max(0.0, image_rect.width * image_rect.height)
            except Exception:
                continue
        return round(area / page_area, 4)
    except Exception:
        return 0.0


class PDFExtractor:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extrai o texto bruto do PDF via PyMuPDF.
        Se a página não contiver texto real (ex: scanneado),
        usa o Tesseract-OCR na imagem gerada.
        """
        extracted_text = ""
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text").strip()
                ratio = _image_area_ratio(page)

                # OCR por cobertura espacial (D07): sem texto, pouco texto
                # ou híbrida (cabeçalho legível + corpo digitalizado).
                if page_needs_ocr(text, ratio):
                    logger.info(f"Página {page_num} parece ser imagem. Iniciando OCR.")
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    # Força linguagem portuguesa se aplicável
                    ocr_text = pytesseract.image_to_string(img, lang="por+eng")
                    extracted_text += ocr_text + "\n"
                else:
                    extracted_text += text + "\n"
                    
            doc.close()
            return extracted_text.strip()
        except Exception as e:
            logger.error(f"Erro na extração do PDF: {str(e)}")
            raise e
