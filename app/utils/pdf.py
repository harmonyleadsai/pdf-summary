import io
import logging
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception as e:
            logger.exception("Error extracting page text: %s", e)
    return "\n".join(texts)
