import io
import os
from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field

from backend.app.knowledge.pdf_parser import PDFParser
from backend.app.knowledge.text_cleaner import TextCleaner
from backend.app.knowledge.section_extractor import SectionExtractor
from backend.app.knowledge.repository import KnowledgeRepository


class DraftKnowledgeObject(BaseModel):
    """
    Represents an in-memory structured draft knowledge object extracted from a source document.
    This is not the final canonical KnowledgeObject stored in the database/repository.
    """
    source_document: str
    section_title: str
    section_number: str
    raw_text: str
    page_number: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PDFIngestionPipeline:
    """
    Orchestrates the ingestion, parsing, cleaning, and section segmenting
    of PDF files into structured DraftKnowledgeObjects.
    """
    def __init__(self, repository: Optional[KnowledgeRepository] = None):
        self.repository = repository or KnowledgeRepository()
        self.parser = PDFParser()
        self.cleaner = TextCleaner()
        self.extractor = SectionExtractor()

    def process(
        self,
        pdf_source: Union[str, bytes, io.BytesIO],
        source_document_name: Optional[str] = None
    ) -> List[DraftKnowledgeObject]:
        """
        Executes the PDF ingestion pipeline stages:
        1. Read PDF & Extract raw text by page
        2. Normalize whitespace and remove headers/footers (where possible)
        3. Split into logical sections using regex heuristics
        4. Generate and return DraftKnowledgeObjects

        Args:
            pdf_source: Filepath, bytes content, or BytesIO stream of the PDF.
            source_document_name: Optional filename to override the default name.

        Returns:
            List[DraftKnowledgeObject]: The structured draft segments.
        """
        # Determine source document name
        if not source_document_name:
            if isinstance(pdf_source, str):
                source_document_name = os.path.basename(pdf_source)
            else:
                source_document_name = "uploaded_document.pdf"

        # Step 1: Read PDF and extract page-by-page text
        pages_data = self.parser.extract_text_by_page(pdf_source)

        # Step 2: Clean text and strip headers/footers
        cleaned_pages = self.cleaner.remove_headers_footers(pages_data)

        # Step 3: Segment into logical sections
        sections_data = self.extractor.extract_sections(cleaned_pages)

        # Step 4: Map to DraftKnowledgeObjects
        draft_objects = []
        for sec in sections_data:
            draft_objects.append(DraftKnowledgeObject(
                source_document=source_document_name,
                section_title=sec["section_title"],
                section_number=sec["section_number"],
                raw_text=sec["raw_text"],
                page_number=sec["page_number"],
                metadata={
                    "total_pages": len(pages_data)
                }
            ))

        return draft_objects
