import os
import json
import pytest
from typing import Generator

from backend.app.knowledge.models import KnowledgeObject, KnowledgeReference
from backend.app.knowledge.repository import KnowledgeRepository
from backend.app.knowledge.validator import KnowledgeValidator


@pytest.fixture
def temp_repo_dir(tmp_path) -> str:
    """
    Returns a temporary directory for knowledge repository testing.
    """
    return str(tmp_path)


def get_mock_object(
    obj_id: str = "obj-1",
    obj_type: str = "license",
    jurisdiction: str = "CA",
    authority: str = "Secretary of State",
    version: str = "1.0.0",
    effective_date: str = "2026-01-01",
    expiry_date: str = None,
) -> KnowledgeObject:
    return KnowledgeObject(
        id=obj_id,
        type=obj_type,
        jurisdiction=jurisdiction,
        authority=authority,
        title=f"Title for {obj_id}",
        description="Description",
        effective_date=effective_date,
        expiry_date=expiry_date,
        version=version,
        source="https://test.gov",
        tags=["test"],
        metadata={"custom": "field"},
    )


# ----------------------------------------------------
# Repository Tests
# ----------------------------------------------------

def test_repo_store_and_load(temp_repo_dir):
    repo = KnowledgeRepository(knowledge_dir=temp_repo_dir)

    obj1 = get_mock_object(obj_id="lic-101", obj_type="license")
    obj2 = get_mock_object(obj_id="auth-202", obj_type="authority")

    # Store
    repo.store(obj1)
    repo.store(obj2)

    # Verify directory structure
    assert os.path.exists(os.path.join(temp_repo_dir, "licenses", "lic-101.json"))
    assert os.path.exists(os.path.join(temp_repo_dir, "authorities", "auth-202.json"))

    # Load all
    all_objs = repo.load_all()
    assert len(all_objs) == 2

    # Lookup by ID
    looked_up = repo.lookup_by_id("lic-101")
    assert looked_up is not None
    assert looked_up.id == "lic-101"
    assert looked_up.type == "license"


def test_repo_lookups_and_updates(temp_repo_dir):
    repo = KnowledgeRepository(knowledge_dir=temp_repo_dir)

    obj1 = get_mock_object(obj_id="lic-1", obj_type="license", jurisdiction="CA", authority="Dept A")
    obj2 = get_mock_object(obj_id="lic-2", obj_type="license", jurisdiction="NY", authority="Dept B")
    obj3 = get_mock_object(obj_id="doc-1", obj_type="document", jurisdiction="CA", authority="Dept A")

    repo.store(obj1)
    repo.store(obj2)
    repo.store(obj3)

    # Clear repository in-memory cache to force loading from disk on lookup
    repo._cache.clear()

    # Lookup by type
    licenses = repo.lookup_by_type("license")
    assert len(licenses) == 2
    assert {l.id for l in licenses} == {"lic-1", "lic-2"}

    # Lookup by jurisdiction
    ca_objs = repo.lookup_by_jurisdiction("CA")
    assert len(ca_objs) == 2
    assert {o.id for o in ca_objs} == {"lic-1", "doc-1"}

    # Lookup by authority
    dept_a_objs = repo.lookup_by_authority("Dept A")
    assert len(dept_a_objs) == 2
    assert {o.id for o in dept_a_objs} == {"lic-1", "doc-1"}

    # Update
    updated_obj = get_mock_object(obj_id="lic-1", obj_type="license", jurisdiction="CA", authority="Dept A", version="2.0.0")
    repo.update(updated_obj)

    loaded_updated = repo.lookup_by_id("lic-1")
    assert loaded_updated.version == "2.0.0"


def test_repo_references(temp_repo_dir):
    repo = KnowledgeRepository(knowledge_dir=temp_repo_dir)

    ref1 = KnowledgeReference(from_id="lic-1", to_id="doc-1", relationship="depends_on")
    ref2 = KnowledgeReference(from_id="doc-1", to_id="auth-1", relationship="governed_by")

    repo.store_references([ref1, ref2])

    # Verify file existence
    assert os.path.exists(os.path.join(temp_repo_dir, "references.json"))

    # Load references
    loaded = repo.load_references()
    assert len(loaded) == 2
    assert loaded[0].from_id == "lic-1"
    assert loaded[1].relationship == "governed_by"


# ----------------------------------------------------
# Validator Tests
# ----------------------------------------------------

def test_validator_success():
    validator = KnowledgeValidator()

    obj1 = get_mock_object(obj_id="lic-1", obj_type="license")
    obj2 = get_mock_object(obj_id="doc-1", obj_type="document")
    ref = KnowledgeReference(from_id="lic-1", to_id="doc-1", relationship="depends_on")

    errors = validator.validate([obj1, obj2], [ref])
    assert len(errors) == 0


def test_validator_duplicate_ids():
    validator = KnowledgeValidator()

    obj1 = get_mock_object(obj_id="same-id", obj_type="license")
    obj2 = get_mock_object(obj_id="same-id", obj_type="document")

    errors = validator.validate([obj1, obj2], [])
    assert len(errors) == 1
    assert "Duplicate ID found: 'same-id'" in errors[0]


def test_validator_unknown_type():
    validator = KnowledgeValidator()

    obj = get_mock_object(obj_id="lic-1", obj_type="invalid_type")

    errors = validator.validate([obj], [])
    assert len(errors) == 1
    assert "has unknown type: 'invalid_type'" in errors[0]


def test_validator_invalid_version():
    validator = KnowledgeValidator()

    # Bad SemVer formatting
    obj1 = get_mock_object(obj_id="lic-1", version="1.0")
    obj2 = get_mock_object(obj_id="lic-2", version="v1.0.0")
    obj3 = get_mock_object(obj_id="lic-3", version="1.a.0")

    errors = validator.validate([obj1, obj2, obj3], [])
    assert len(errors) == 3
    assert all("has invalid version format" in err for err in errors)


def test_validator_invalid_dates():
    validator = KnowledgeValidator()

    # Bad dates
    obj1 = get_mock_object(obj_id="lic-1", effective_date="2026/01/01")
    obj2 = get_mock_object(obj_id="lic-2", effective_date="2026-01-01", expiry_date="invalid-date")
    # Expiry before effective date
    obj3 = get_mock_object(obj_id="lic-3", effective_date="2026-06-01", expiry_date="2026-01-01")

    errors = validator.validate([obj1, obj2, obj3], [])
    assert len(errors) == 3
    assert "invalid effective_date format" in errors[0]
    assert "invalid expiry_date format" in errors[1]
    assert "expiry_date '2026-01-01' is before effective_date '2026-06-01'" in errors[2]


def test_validator_missing_references():
    validator = KnowledgeValidator()

    obj1 = get_mock_object(obj_id="lic-1")
    ref = KnowledgeReference(from_id="lic-1", to_id="doc-999", relationship="depends_on")

    errors = validator.validate([obj1], [ref])
    assert len(errors) == 1
    assert "Reference to_id 'doc-999' points to a non-existent object ID" in errors[0]
