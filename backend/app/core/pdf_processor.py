import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

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
                
                # Se não contem texto suficiente, tenta OCR
                if len(text) < 50:
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
