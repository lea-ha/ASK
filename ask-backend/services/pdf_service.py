import PyPDF2
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        pass
    
    def extract_text_from_file(self, file):
        """Extract text from uploaded PDF file"""
        try:
            pdf_data = BytesIO(file.read())
            return self.extract_text_from_pdf(pdf_data)
        except Exception as e:
            logger.error(f"Error extracting text from file: {e}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_data):
        """Extract text from PDF BytesIO object"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_data)
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
            
            if not text.strip():
                raise Exception("No text could be extracted from the PDF")
                
            return text.strip()
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise Exception(f"Failed to process PDF: {str(e)}")