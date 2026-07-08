import io
import pytest
from reportlab.pdfgen import canvas

from backend.app.knowledge.pdf_parser import PDFParser, PDFParserError
from backend.app.knowledge.text_cleaner import TextCleaner
from backend.app.knowledge.section_extractor import SectionExtractor
from backend.app.knowledge.pipeline import PDFIngestionPipeline, DraftKnowledgeObject


def generate_test_pdf(
    pages_content: list[list[str]],
    header: str = "",
    footer_pattern: str = "Page {}"
) -> bytes:
    """
    Generates a PDF in-memory using reportlab.
    Each element of pages_content is a list of lines to draw on that page.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    
    for page_idx, lines in enumerate(pages_content):
        y = 800
        # Draw header
        if header:
            c.drawString(100, y, header)
            y -= 40
            
        # Draw body lines
        for line in lines:
            c.drawString(100, y, line)
            y -= 30
            
        # Draw footer/page number
        if footer_pattern:
            c.drawString(100, 50, footer_pattern.format(page_idx + 1))
            
        c.showPage()
        
    c.save()
    return buffer.getvalue()


# =====================================================================
# PDF Parser Tests
# =====================================================================

def test_pdf_parser_success():
    """Tests that PDFParser successfully extracts page-by-page text from valid PDF bytes."""
    pages = [
        ["Line 1 on page 1", "Line 2 on page 1"],
        ["Line 1 on page 2", "Another line"]
    ]
    pdf_bytes = generate_test_pdf(pages, header="Document Header", footer_pattern="Page {}")
    
    parser = PDFParser()
    pages_data = parser.extract_text_by_page(pdf_bytes)
    
    assert len(pages_data) == 2
    assert pages_data[0]["page_number"] == 1
    assert "Line 1 on page 1" in pages_data[0]["text"]
    assert "Document Header" in pages_data[0]["text"]
    
    assert pages_data[1]["page_number"] == 2
    assert "Line 1 on page 2" in pages_data[1]["text"]


def test_pdf_parser_malformed():
    """Tests that PDFParser raises PDFParserError when given malformed PDF bytes."""
    parser = PDFParser()
    with pytest.raises(PDFParserError):
        parser.extract_text_by_page(b"This is completely invalid PDF content.")


def test_pdf_parser_empty():
    """Tests that PDFParser raises PDFParserError when given empty bytes."""
    parser = PDFParser()
    with pytest.raises(PDFParserError):
        parser.extract_text_by_page(b"")


# =====================================================================
# Text Cleaner Tests
# =====================================================================

def test_text_cleaner_normalize():
    """Tests basic text normalization including whitespace collapsing and unicode normalization."""
    cleaner = TextCleaner()
    
    # 1. Unicode fraction 1/2 normalization to '1/2' or NFKC equivalent '1/2'
    raw_unicode = "Value is \u00bd." # 1/2 fraction symbol
    normalized = cleaner.normalize_text(raw_unicode)
    assert normalized == "Value is 1\u20442."
    
    # 2. Line ending normalization (\r\n -> \n)
    raw_newlines = "Line 1\r\nLine 2\rLine 3"
    assert cleaner.normalize_text(raw_newlines) == "Line 1\nLine 2\nLine 3"
    
    # 3. Collapse multiple spaces and tabs
    raw_spaces = "Section    3.1 \t\t  Eligibility    Requirements   "
    assert cleaner.normalize_text(raw_spaces) == "Section 3.1 Eligibility Requirements"

    # 4. Limit consecutive blank lines
    raw_blank_lines = "Paragraph 1\n\n\n\nParagraph 2\n\nParagraph 3"
    assert cleaner.normalize_text(raw_blank_lines) == "Paragraph 1\n\nParagraph 2\n\nParagraph 3"


def test_text_cleaner_header_footer_removal():
    """Tests that repeating headers/footers and page numbers are removed across pages."""
    cleaner = TextCleaner()
    
    pages_data = [
        {
            "page_number": 1,
            "text": "Civora AI Compliance Guide\nSome text on first page\nPage 1"
        },
        {
            "page_number": 2,
            "text": "Civora AI Compliance Guide\nMore text on second page\nPage 2"
        },
        {
            "page_number": 3,
            "text": "Civora AI Compliance Guide\nThird page body text\nPage 3"
        }
    ]
    
    cleaned = cleaner.remove_headers_footers(pages_data)
    
    assert len(cleaned) == 3
    # Header "Civora AI Compliance Guide" should be removed
    # Footer "Page X" should be removed
    assert "Civora AI" not in cleaned[0]["text"]
    assert "Page 1" not in cleaned[0]["text"]
    assert "Some text on first page" in cleaned[0]["text"]
    
    assert "Civora AI" not in cleaned[1]["text"]
    assert "Page 2" not in cleaned[1]["text"]
    assert "More text on second page" in cleaned[1]["text"]


# =====================================================================
# Section Extractor Tests
# =====================================================================

def test_section_extractor_matching():
    """Tests that SectionExtractor correctly identifies and segments sections based on headers."""
    extractor = SectionExtractor()
    
    # We will pass flattened pages data containing various header formats
    pages_data = [
        {
            "page_number": 1,
            "text": (
                "Preamble text\n"
                "This is the introduction.\n"
                "Article I - General Scope\n"
                "This is body text for Article I.\n"
                "Section 3.1 Eligibility Criteria\n"
                "Eligible businesses must be small."
            )
        },
        {
            "page_number": 2,
            "text": (
                "Chapter 5 Penalties\n"
                "Fines are up to $500.\n"
                "II. DEFINITIONS\n"
                "Terms are defined below.\n"
                "5.2.1 Reporting Frequency\n"
                "Reports are due monthly."
            )
        }
    ]
    
    sections = extractor.extract_sections(pages_data)
    
    # Expected Sections:
    # 0. Preamble (Preamble text / This is the introduction.)
    # 1. Article I - General Scope
    # 2. Section 3.1 Eligibility Criteria
    # 3. Chapter 5 Penalties
    # 4. II. DEFINITIONS
    # 5. 5.2.1 Reporting Frequency
    
    assert len(sections) == 6
    
    # Preamble check
    assert sections[0]["section_title"] == "Preamble"
    assert sections[0]["section_number"] == "0"
    assert "Preamble text" in sections[0]["raw_text"]
    assert sections[0]["page_number"] == 1
    
    # Article I check
    assert sections[1]["section_title"] == "Article I: General Scope"
    assert sections[1]["section_number"] == "I"
    assert "This is body text for Article I" in sections[1]["raw_text"]
    assert sections[1]["page_number"] == 1
    
    # Section 3.1 check
    assert sections[2]["section_title"] == "Section 3.1: Eligibility Criteria"
    assert sections[2]["section_number"] == "3.1"
    assert "Eligible businesses must be small" in sections[2]["raw_text"]
    assert sections[2]["page_number"] == 1
    
    # Chapter 5 check
    assert sections[3]["section_title"] == "Chapter 5: Penalties"
    assert sections[3]["section_number"] == "5"
    assert "Fines are up to $500" in sections[3]["raw_text"]
    assert sections[3]["page_number"] == 2
    
    # Roman numeral check
    assert sections[4]["section_title"] == "II. DEFINITIONS"
    assert sections[4]["section_number"] == "II"
    assert "Terms are defined below" in sections[4]["raw_text"]
    assert sections[4]["page_number"] == 2
    
    # Hierarchical section check
    assert sections[5]["section_title"] == "5.2.1 Reporting Frequency"
    assert sections[5]["section_number"] == "5.2.1"
    assert "Reports are due monthly" in sections[5]["raw_text"]
    assert sections[5]["page_number"] == 2


# =====================================================================
# End-to-End Pipeline Tests
# =====================================================================

def test_pipeline_end_to_end():
    """Tests the full PDFIngestionPipeline from raw PDF bytes to DraftKnowledgeObjects."""
    pages = [
        [
            "Civora AI Guide", # Header (repeating)
            "Preamble content for testing the pipeline.",
            "Article I - Scope and Application",
            "This article governs the entire scope of the pipeline.",
            "Page 1" # Footer (repeating pattern)
        ],
        [
            "Civora AI Guide", # Header (repeating)
            "Section 3.2.1 Technical Specifications",
            "The pipeline runs deterministically in memory.",
            "Page 2" # Footer (repeating pattern)
        ]
    ]
    
    pdf_bytes = generate_test_pdf(pages, header="", footer_pattern="")
    # Note: we manually added header/footer text to pages list, so generate_test_pdf shouldn't overlay duplicates.
    
    pipeline = PDFIngestionPipeline()
    drafts = pipeline.process(pdf_bytes, source_document_name="test_doc.pdf")
    
    assert len(drafts) == 3 # Preamble, Article I, Section 3.2.1
    
    # Check types
    for draft in drafts:
        assert isinstance(draft, DraftKnowledgeObject)
        assert draft.source_document == "test_doc.pdf"
        assert "total_pages" in draft.metadata
        assert draft.metadata["total_pages"] == 2
        
    # Preamble check (should have header stripped if repeated, but here they are explicitly added)
    # Since they repeat on both pages:
    # "Civora AI Guide" is in line 0 of both pages -> stripped
    # "Page 1" / "Page 2" matches page number pattern -> stripped
    
    # Preamble
    assert drafts[0].section_title == "Preamble"
    assert "Preamble content for testing" in drafts[0].raw_text
    assert "Civora AI Guide" not in drafts[0].raw_text
    
    # Article I
    assert drafts[1].section_title == "Article I: Scope and Application"
    assert drafts[1].section_number == "I"
    assert "This article governs" in drafts[1].raw_text
    
    # Section 3.2.1
    assert drafts[2].section_title == "Section 3.2.1: Technical Specifications"
    assert drafts[2].section_number == "3.2.1"
    assert "The pipeline runs deterministically" in drafts[2].raw_text
