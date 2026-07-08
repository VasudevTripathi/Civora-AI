import pytest
from backend.app.knowledge.pipeline import DraftKnowledgeObject
from backend.app.knowledge.normalizer import KnowledgeNormalizer, NormalizationError
from backend.app.knowledge.models import KnowledgeObject
from backend.app.knowledge.validator import KnowledgeValidator


def get_base_draft(
    title: str = "Section 3.1 Eligibility Requirements",
    number: str = "3.1",
    text: str = "Body text here.",
    source: str = "compliance_doc.pdf",
    metadata: dict = None
) -> DraftKnowledgeObject:
    return DraftKnowledgeObject(
        source_document=source,
        section_title=title,
        section_number=number,
        raw_text=text,
        page_number=3,
        metadata=metadata or {}
    )


# =====================================================================
# Whitespace and Title Normalization Tests
# =====================================================================

def test_whitespace_and_title_normalization():
    """Tests cleanup of spaces and special chars in titles and multi-paragraph description text."""
    normalizer = KnowledgeNormalizer()
    
    draft = get_base_draft(
        title="  Section   4.2:   Reporting   Requirements. -:  ",
        text="   Paragraph 1 \t content.  \n\n\n  Paragraph 2 content.   "
    )
    
    obj = normalizer.normalize(draft, type="rule", jurisdiction="KA", authority="Department of Finance")
    
    assert obj.title == "Section 4.2: Reporting Requirements"
    assert obj.description == "Paragraph 1 content.\n\nParagraph 2 content."


# =====================================================================
# Authority Normalization Tests
# =====================================================================

def test_authority_normalization():
    """Tests standardizing casing and expanding common abbreviations (e.g. dept., govt.) in authority names."""
    normalizer = KnowledgeNormalizer()
    
    # Test abbreviation expansion and title casing
    draft = get_base_draft()
    obj = normalizer.normalize(
        draft,
        type="license",
        jurisdiction="NY",
        authority="dept. of state, div. of corporations"
    )
    
    assert obj.authority == "Department Of State, Division Of Corporations"
    
    # Test plain text standardization
    obj2 = normalizer.normalize(
        draft,
        type="license",
        jurisdiction="NY",
        authority="  GOVT   OF   KARNATAKA   "
    )
    assert obj2.authority == "Government Of Karnataka"


# =====================================================================
# Jurisdiction Normalization Tests
# =====================================================================

def test_jurisdiction_normalization():
    """Tests mapping full names to short state/federal codes or falling back to uppercase."""
    normalizer = KnowledgeNormalizer()
    draft = get_base_draft()
    
    # Test mapped jurisdiction (e.g. california -> CA)
    obj_ca = normalizer.normalize(draft, type="act", jurisdiction="california", authority="State")
    assert obj_ca.jurisdiction == "CA"
    
    # Test case insensitivity
    obj_ka = normalizer.normalize(draft, type="act", jurisdiction="  KaRnaTaKa  ", authority="State")
    assert obj_ka.jurisdiction == "KA"
    
    # Test fallback to uppercase
    obj_custom = normalizer.normalize(draft, type="act", jurisdiction="tx-austin", authority="State")
    assert obj_custom.jurisdiction == "TX-AUSTIN"


# =====================================================================
# Version and Date Normalization Tests
# =====================================================================

def test_version_and_date_normalization():
    """Tests SemVer coercion and date standardizing (converting to YYYY-MM-DD)."""
    normalizer = KnowledgeNormalizer()
    draft = get_base_draft()
    
    # Test version prefix strip and extension
    obj = normalizer.normalize(
        draft,
        version=" v2.1 ",
        effective_date=" 15/04/2026 ",
        expiry_date=" 2026-12-31T23:59:59Z "
    )
    assert obj.version == "2.1.0"
    assert obj.effective_date == "2026-04-15"
    assert obj.expiry_date == "2026-12-31"
    
    # Test invalid date formatting raises NormalizationError
    with pytest.raises(NormalizationError):
        normalizer.normalize(draft, effective_date="invalid-date-string")


# =====================================================================
# Metadata Snake Case Conversion Tests
# =====================================================================

def test_metadata_snake_case_conversion():
    """Tests that custom metadata keys are converted from camelCase/dot.notation/spaces to snake_case."""
    normalizer = KnowledgeNormalizer()
    
    draft = get_base_draft(metadata={
        "customKey": "value1",
        "nested.Dot.Key": {"subKeyName": "value2"},
        "space key name": "value3"
    })
    
    obj = normalizer.normalize(draft, type="rule")
    
    metadata = obj.metadata
    assert "custom_key" in metadata
    assert metadata["custom_key"] == "value1"
    
    assert "nested_dot_key" in metadata
    assert "sub_key_name" in metadata["nested_dot_key"]
    assert metadata["nested_dot_key"]["sub_key_name"] == "value2"
    
    assert "space_key_name" in metadata
    assert metadata["space_key_name"] == "value3"


# =====================================================================
# Traceability Preservation Tests
# =====================================================================

def test_traceability_preservation():
    """Tests that original source, page, section, and original metadata are retained."""
    normalizer = KnowledgeNormalizer()
    
    original_meta = {"confidence": 0.95, "type": "rule", "jurisdiction": "KA"}
    draft = get_base_draft(
        title="Article II - General Provisions",
        number="II",
        text="Content of section",
        source="specifications.pdf",
        metadata=original_meta
    )
    
    obj = normalizer.normalize(draft, type="rule", jurisdiction="KA", authority="Govt Auth")
    
    # Assert original values are in the traceability field
    trace = obj.metadata.get("traceability")
    assert trace is not None
    assert trace["original_source"] == "specifications.pdf"
    assert trace["original_section_title"] == "Article II - General Provisions"
    assert trace["original_section_number"] == "II"
    assert trace["original_page"] == 3
    assert trace["original_metadata"] == original_meta


# =====================================================================
# Validator Compatibility Tests
# =====================================================================

def test_validator_compatibility():
    """Tests that normalizer validates output using KnowledgeValidator and raises on fail."""
    validator = KnowledgeValidator()
    normalizer = KnowledgeNormalizer(validator=validator)
    
    # 1. Valid inputs should pass the validator silently
    draft = get_base_draft()
    obj = normalizer.normalize(draft, type="license", jurisdiction="CA", authority="Sec State")
    
    errors = validator.validate([obj], [])
    assert len(errors) == 0
    
    # 2. Invalid inputs (e.g. expiry before effective date) should fail validation
    # and cause normalizer to raise NormalizationError
    with pytest.raises(NormalizationError):
        normalizer.normalize(
            draft,
            type="license",
            jurisdiction="CA",
            authority="Sec State",
            effective_date="2026-06-01",
            expiry_date="2026-01-01"
        )
