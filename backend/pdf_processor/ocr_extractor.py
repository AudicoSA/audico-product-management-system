import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from typing import Dict, List
import os
import tempfile

class OCRExtractor:
    """Extract text from PDF files using OCR"""

    def __init__(self):
        # Configure Tesseract path if needed (Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass

    def extract_text_from_pdf(self, pdf_path: str) -> Dict:
        """Extract text from PDF using multiple methods"""
        try:
            # Method 1: Try direct text extraction first (faster)
            text_content = self._extract_direct_text(pdf_path)

            if text_content and len(text_content.strip()) > 100:
                return {
                    'success': True,
                    'method': 'direct_extraction',
                    'text': text_content,
                    'page_count': self._get_page_count(pdf_path)
                }

            # Method 2: Use OCR if direct extraction fails
            ocr_text = self._extract_ocr_text(pdf_path)

            return {
                'success': True,
                'method': 'ocr_extraction',
                'text': ocr_text,
                'page_count': self._get_page_count(pdf_path)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Text extraction failed: {str(e)}'
            }

    def _extract_direct_text(self, pdf_path: str) -> str:
        """Extract text directly from PDF"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    def _extract_ocr_text(self, pdf_path: str) -> str:
        """Extract text using OCR"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)

            text = ""
            for i, image in enumerate(images):
                # Use Tesseract to extract text from image
                page_text = pytesseract.image_to_string(image)
                text += f"--- Page {i+1} ---\n{page_text}\n\n"

            return text

        except Exception as e:
            return f"OCR extraction failed: {str(e)}"

    def _get_page_count(self, pdf_path: str) -> int:
        """Get number of pages in PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except:
            return 0
