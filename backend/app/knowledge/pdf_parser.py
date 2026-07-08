import os
import io
import pypdf
from typing import List, Dict, Any, Union
from loguru import logger


class PDFParserError(Exception):
    """Exception raised during PDF parsing failures."""
    pass


class PDFParser:
    """
    Handles deterministic reading and text extraction from PDF files or byte streams.
    """
    def extract_text_by_page(self, pdf_source: Union[str, bytes, io.BytesIO]) -> List[Dict[str, Any]]:
        """
        Reads a PDF from a filepath, raw bytes, or BytesIO object, and extracts text page-by-page.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing each page:
                [
                    {"page_number": 1, "text": "Page 1 content..."},
                    {"page_number": 2, "text": "Page 2 content..."},
                ]

        Raises:
            FileNotFoundError: If a filepath is provided but does not exist.
            PDFParserError: If the PDF is malformed, corrupted, empty, or encrypted.
        """
        stream = None
        should_close = False

        try:
            if isinstance(pdf_source, str):
                if not os.path.exists(pdf_source):
                    raise FileNotFoundError(f"PDF file not found at path: {pdf_source}")
                stream = open(pdf_source, "rb")
                should_close = True
            elif isinstance(pdf_source, bytes):
                stream = io.BytesIO(pdf_source)
            elif isinstance(pdf_source, io.BytesIO):
                stream = pdf_source
            else:
                raise TypeError(
                    f"Unsupported PDF source type: {type(pdf_source)}. "
                    f"Must be a str path, bytes, or io.BytesIO."
                )

            reader = pypdf.PdfReader(stream)

            # Check encryption
            if reader.is_encrypted:
                try:
                    # Attempt decryption with an empty password
                    reader.decrypt("")
                except Exception as e:
                    raise PDFParserError(f"PDF is encrypted and could not be decrypted: {e}")

            num_pages = len(reader.pages)
            if num_pages == 0:
                raise PDFParserError("PDF file contains no pages.")

            pages_data = []
            for idx in range(num_pages):
                page_number = idx + 1
                try:
                    page = reader.pages[idx]
                    text = page.extract_text() or ""
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_number}: {e}")
                    text = ""
                
                pages_data.append({
                    "page_number": page_number,
                    "text": text
                })

            return pages_data

        except pypdf.errors.PdfReadError as e:
            raise PDFParserError(f"Malformed or invalid PDF: {e}")
        except Exception as e:
            if isinstance(e, (PDFParserError, FileNotFoundError, TypeError)):
                raise
            raise PDFParserError(f"Failed to parse PDF: {e}")
        finally:
            if should_close and stream:
                stream.close()
