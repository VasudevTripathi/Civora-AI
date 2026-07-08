import os
import pytest
from backend.app.knowledge.repository import KnowledgeRepository
from backend.app.knowledge.validator import KnowledgeValidator
from backend.app.services.knowledge_loader import KnowledgeLoader


@pytest.fixture
def prod_knowledge_dir() -> str:
    """
    Returns the absolute path to the production knowledge directory.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "data", "knowledge")


def test_delaware_llc_repository_validation(prod_knowledge_dir):
    """
    Verifies that the KnowledgeRepository loads all objects and references successfully,
    and the KnowledgeValidator returns zero validation errors.
    """
    repo = KnowledgeRepository(knowledge_dir=prod_knowledge_dir)
    objects = repo.load_all()
    references = repo.load_references()

    # Verify we successfully loaded Delaware LLC objects
    delaware_uuids = {
        "8e8d89e5-9c88-469b-8e1d-384a28bb0001",  # Business
        "8e8d89e5-9c88-469b-8e1d-384a28bb0002",  # Corp Authority
        "8e8d89e5-9c88-469b-8e1d-384a28bb0004",  # Revenue Authority
        "8e8d89e5-9c88-469b-8e1d-384a28bb0005",  # Cert of Formation
        "8e8d89e5-9c88-469b-8e1d-384a28bb0006",  # General Business License
        "8e8d89e5-9c88-469b-8e1d-384a28bb0010",  # Cert of Formation Timeline
        "8e8d89e5-9c88-469b-8e1d-384a28bb0011",  # General Business License Timeline
        "8e8d89e5-9c88-469b-8e1d-384a28bb0012",  # Cert of Formation Fee
        "8e8d89e5-9c88-469b-8e1d-384a28bb0013",  # General Business License Fee
        "8e8d89e5-9c88-469b-8e1d-384a28bb0015",  # Cert of Formation PDF
        "8e8d89e5-9c88-469b-8e1d-384a28bb0016",  # Registered Agent Consent PDF
        "8e8d89e5-9c88-469b-8e1d-384a28bb0020",  # Formation Rule
        "8e8d89e5-9c88-469b-8e1d-384a28bb0099",  # LLC Act
        "8e8d89e5-9c88-469b-8e1d-384a28bb0019",  # Annual tax renewal deadline
    }

    loaded_ids = {obj.id for obj in objects}
    for uuid in delaware_uuids:
        assert uuid in loaded_ids, f"Expected object {uuid} was not loaded by the repository."

    # Validate using the KnowledgeValidator (ensures no duplicate IDs and no broken references)
    validator = KnowledgeValidator()
    errors = validator.validate(objects, references)

    assert len(errors) == 0, f"Validation failed with errors: {errors}"


def test_delaware_llc_schema_validation(prod_knowledge_dir):
    """
    Verifies that all Delaware LLC knowledge files comply fully with their JSON schemas.
    """
    loader = KnowledgeLoader(knowledge_dir=prod_knowledge_dir)

    # 1. Businesses
    biz = loader.load_file("businesses", "delaware_llc.json")
    assert biz["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0001"
    assert biz["business_type"] == "LLC"
    assert biz["applicable_state"] == "DE"

    # 2. Authorities
    corp_auth = loader.load_file("authorities", "delaware_division_of_corporations.json")
    assert corp_auth["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0002"
    assert corp_auth["jurisdiction"] == "State"

    rev_auth = loader.load_file("authorities", "delaware_division_of_revenue.json")
    assert rev_auth["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0004"
    assert rev_auth["jurisdiction"] == "State"

    # 3. Licenses
    cert_form = loader.load_file("licenses", "certificate_of_formation.json")
    assert cert_form["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0005"
    assert cert_form["timeline_uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0010"

    biz_lic = loader.load_file("licenses", "delaware_general_business_license.json")
    assert biz_lic["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0006"
    assert biz_lic["timeline_uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0011"

    # 4. Timelines
    timeline_1 = loader.load_file("timelines", "certificate_of_formation_timeline.json")
    assert timeline_1["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0010"
    assert timeline_1["processing_duration_days"] == 5

    timeline_2 = loader.load_file("timelines", "general_business_license_timeline.json")
    assert timeline_2["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0011"
    assert timeline_2["processing_duration_days"] == 10

    # 5. Fees
    fee_1 = loader.load_file("fees", "certificate_of_formation_fee.json")
    assert fee_1["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0012"
    assert fee_1["fee_amount"] == 90.0

    fee_2 = loader.load_file("fees", "general_business_license_fee.json")
    assert fee_2["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0013"
    assert fee_2["fee_amount"] == 75.0

    # 6. Documents
    doc_1 = loader.load_file("documents", "certificate_of_formation_pdf.json")
    assert doc_1["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0015"
    assert doc_1["document_name"] == "Delaware LLC Certificate of Formation Form"

    doc_2 = loader.load_file("documents", "registered_agent_consent.json")
    assert doc_2["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0016"
    assert doc_2["document_name"] == "Registered Agent Consent Form"

    # 7. Rules
    rule_1 = loader.load_file("rules", "delaware_llc_rule.json")
    assert rule_1["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0020"
    assert rule_1["legal_act_uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0099"

    # 8. Acts
    act_1 = loader.load_file("acts", "delaware_llc_act.json")
    assert act_1["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0099"
    assert act_1["act_name"] == "Delaware Limited Liability Company Act"

    # 9. Deadlines / Renewals
    deadline_1 = loader.load_file("deadlines", "delaware_annual_tax_deadline.json")
    assert deadline_1["uuid"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0019"
    assert deadline_1["recurrence_months"] == 12
