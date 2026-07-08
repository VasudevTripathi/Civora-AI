import os
import pytest
from unittest.mock import MagicMock

from backend.app.knowledge.pipeline import DraftKnowledgeObject
from backend.app.knowledge.normalizer import KnowledgeNormalizer
from backend.app.knowledge.validator import KnowledgeValidator
from backend.app.knowledge.repository import KnowledgeRepository
from backend.app.knowledge.orchestrator import KnowledgeIngestionOrchestrator, IngestionResult


@pytest.fixture
def temp_repo(tmp_path) -> KnowledgeRepository:
    """Fixture returning a KnowledgeRepository pointed to a temporary directory."""
    return KnowledgeRepository(knowledge_dir=str(tmp_path))


def get_draft(
    title: str = "Draft Title",
    number: str = "1.0",
    text: str = "Body content.",
    metadata: dict = None
) -> DraftKnowledgeObject:
    return DraftKnowledgeObject(
        source_document="test_doc.pdf",
        section_title=title,
        section_number=number,
        raw_text=text,
        page_number=1,
        metadata=metadata or {}
    )


# =====================================================================
# Successful Ingestion Tests
# =====================================================================

def test_orchestrator_success(temp_repo):
    """Tests that a batch of valid drafts is successfully processed and stored."""
    orchestrator = KnowledgeIngestionOrchestrator(repository=temp_repo)
    
    drafts = [
        get_draft(title="Article I - General Provisions", number="I", text="Content 1"),
        get_draft(title="Section 3.1 Eligibility Requirements", number="3.1", text="Content 2")
    ]
    
    result = orchestrator.ingest(
        drafts,
        type="license",
        jurisdiction="KA",
        authority="Secretary of State"
    )
    
    assert isinstance(result, IngestionResult)
    assert result.processed_objects == 2
    assert len(result.successful_objects) == 2
    assert len(result.failed_objects) == 0
    assert len(result.validation_errors) == 0
    assert result.processing_time_ms >= 0
    assert "Ingested 2/2 objects successfully" in result.summary

    # Verify files actually exist in the temp repository
    stored_all = temp_repo.load_all()
    assert len(stored_all) == 2
    ids = {obj.id for obj in stored_all}
    assert "license-ka-secretary-of-state-i" in ids
    assert "license-ka-secretary-of-state-3-1" in ids


# =====================================================================
# Partial Ingestion Failures Tests
# =====================================================================

def test_orchestrator_partial_failures(temp_repo):
    """Tests that a single bad draft is isolated and remaining valid drafts succeed."""
    orchestrator = KnowledgeIngestionOrchestrator(repository=temp_repo)
    
    drafts = [
        # 1. Valid Draft
        get_draft(title="Article I - General Provisions", number="I", text="Content 1"),
        # 2. Invalid Draft (malformed date will trigger NormalizationError)
        get_draft(title="Invalid Section", number="II", text="Content 2", metadata={"effective_date": "bad-date"}),
        # 3. Valid Draft
        get_draft(title="Section 3.1 Eligibility Requirements", number="3.1", text="Content 3")
    ]
    
    result = orchestrator.ingest(
        drafts,
        type="license",
        jurisdiction="KA",
        authority="Secretary of State"
    )
    
    assert result.processed_objects == 3
    assert len(result.successful_objects) == 2
    assert len(result.failed_objects) == 1
    assert result.failed_objects[0] == "Invalid Section"
    
    # Assert validation error captures normalizer error message
    assert len(result.validation_errors) == 1
    assert result.validation_errors[0]["section_title"] == "Invalid Section"
    assert "Invalid effective_date" in result.validation_errors[0]["errors"][0]

    # Verify only the 2 valid files are stored
    stored_all = temp_repo.load_all()
    assert len(stored_all) == 2


# =====================================================================
# Validation Failures Tests
# =====================================================================

def test_orchestrator_validation_failures(temp_repo):
    """Tests validation constraints violation (e.g. expiry before effective date)."""
    orchestrator = KnowledgeIngestionOrchestrator(repository=temp_repo)
    
    drafts = [
        get_draft(
            title="Expired License",
            number="1.0",
            text="Body text",
            metadata={
                "effective_date": "2026-06-01",
                "expiry_date": "2026-01-01" # expiry before effective is checked in KnowledgeValidator
            }
        )
    ]
    
    result = orchestrator.ingest(
        drafts,
        type="license",
        jurisdiction="NY",
        authority="State Office"
    )
    
    assert result.processed_objects == 1
    assert len(result.successful_objects) == 0
    assert len(result.failed_objects) == 1
    assert result.failed_objects[0] == "Expired License"
    
    assert len(result.validation_errors) == 1
    assert "expiry_date" in result.validation_errors[0]["errors"][0]
    assert "is before effective_date" in result.validation_errors[0]["errors"][0]

    stored_all = temp_repo.load_all()
    assert len(stored_all) == 0


# =====================================================================
# Repository Failures Tests
# =====================================================================

def test_orchestrator_repository_failures():
    """Tests that repository write failures (e.g. IOError/disk full) are isolated and handled."""
    failing_repo = MagicMock(spec=KnowledgeRepository)
    failing_repo.store.side_effect = IOError("Disk full or permission denied")
    
    orchestrator = KnowledgeIngestionOrchestrator(repository=failing_repo)
    draft = get_draft(title="My Article", number="1")
    
    result = orchestrator.ingest(
        [draft],
        type="license",
        jurisdiction="CA",
        authority="Secretary of State"
    )
    
    assert result.processed_objects == 1
    assert len(result.successful_objects) == 0
    assert len(result.failed_objects) == 1
    assert result.failed_objects[0] == "My Article"
    
    assert len(result.validation_errors) == 1
    assert "Storage failure" in result.validation_errors[0]["errors"][0]
    assert "Disk full" in result.validation_errors[0]["errors"][0]


# =====================================================================
# Large Batches Tests
# =====================================================================

def test_orchestrator_large_batch(temp_repo):
    """Tests processing of a large batch (e.g. 50 drafts) to ensure scalability."""
    orchestrator = KnowledgeIngestionOrchestrator(repository=temp_repo)
    
    drafts = []
    for idx in range(50):
        drafts.append(get_draft(
            title=f"Section {idx}",
            number=str(idx),
            text=f"Content batch {idx}"
        ))
        
    result = orchestrator.ingest(
        drafts,
        type="license",
        jurisdiction="KA",
        authority="Secretary of State"
    )
    
    assert result.processed_objects == 50
    assert len(result.successful_objects) == 50
    assert len(result.failed_objects) == 0
    assert len(result.validation_errors) == 0

    stored_all = temp_repo.load_all()
    assert len(stored_all) == 50
