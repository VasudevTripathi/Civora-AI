import os
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.app.core.config import Settings
from backend.app.core.dependencies import get_settings


@pytest.fixture
def api_client():
    """
    Returns a TestClient pointing to the production knowledge pack data.
    """
    # Go up 3 levels from backend/tests/test_api.py to reach the root workspace directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    prod_dir = os.path.join(base_dir, "data", "knowledge")
    
    prod_settings = Settings(
        ENV="testing",
        KNOWLEDGE_DIR=prod_dir
    )
    
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: prod_settings
    
    # Temporarily patch the dependency singletons for clean testing
    from backend.app.core import dependencies
    original_repo = dependencies._knowledge_repository
    original_policy = dependencies._policy_loader
    original_knowledge = dependencies._knowledge_loader
    
    from backend.app.knowledge.repository import KnowledgeRepository
    from backend.app.services.policy_loader import PolicyLoader
    from backend.app.services.knowledge_loader import KnowledgeLoader
    
    dependencies._knowledge_repository = KnowledgeRepository(knowledge_dir=prod_dir)
    dependencies._policy_loader = PolicyLoader(knowledge_dir=prod_dir)
    dependencies._knowledge_loader = KnowledgeLoader(knowledge_dir=prod_dir)
    
    # Propagate the patched loaders to the existing engine singletons
    dependencies._rule_engine.policy_loader = dependencies._policy_loader
    dependencies._rule_engine.rules = []
    
    dependencies._evaluator.policy_loader = dependencies._policy_loader
    dependencies._eligibility_engine.policy_loader = dependencies._policy_loader
    dependencies._workflow_engine.policy_loader = dependencies._policy_loader
    dependencies._workflow_engine.knowledge_loader = dependencies._knowledge_loader
    
    dependencies._compliance_engine.policy_loader = dependencies._policy_loader
    dependencies._compliance_engine.knowledge_loader = dependencies._knowledge_loader
    dependencies._compliance_engine.rule_engine = dependencies._rule_engine
    dependencies._compliance_engine.evaluator = dependencies._evaluator
    dependencies._compliance_engine.eligibility_engine = dependencies._eligibility_engine
    dependencies._compliance_engine.workflow_engine = dependencies._workflow_engine
    
    with TestClient(app) as client:
        yield client
        
    # Restore original singletons
    dependencies._knowledge_repository = original_repo
    dependencies._policy_loader = original_policy
    dependencies._knowledge_loader = original_knowledge
    
    dependencies._rule_engine.policy_loader = original_policy
    dependencies._rule_engine.rules = []
    dependencies._evaluator.policy_loader = original_policy
    dependencies._eligibility_engine.policy_loader = original_policy
    dependencies._workflow_engine.policy_loader = original_policy
    dependencies._workflow_engine.knowledge_loader = original_knowledge
    
    dependencies._compliance_engine.policy_loader = original_policy
    dependencies._compliance_engine.knowledge_loader = original_knowledge
    dependencies._compliance_engine.rule_engine = dependencies._rule_engine
    dependencies._compliance_engine.evaluator = dependencies._evaluator
    dependencies._compliance_engine.eligibility_engine = dependencies._eligibility_engine
    dependencies._compliance_engine.workflow_engine = dependencies._workflow_engine


def test_api_health_endpoint(api_client):
    """
    Verifies that the GET /health endpoint functions correctly.
    """
    response = api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_api_knowledge_businesses(api_client):
    """
    Verifies GET /knowledge/businesses returns Delaware LLC profile.
    """
    response = api_client.get("/knowledge/businesses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(b["id"] == "8e8d89e5-9c88-469b-8e1d-384a28bb0001" for b in data)


def test_api_knowledge_licenses(api_client):
    """
    Verifies GET /knowledge/licenses returns Delaware LLC license requirements.
    """
    response = api_client.get("/knowledge/licenses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    license_ids = {lic["id"] for lic in data}
    assert "8e8d89e5-9c88-469b-8e1d-384a28bb0005" in license_ids
    assert "8e8d89e5-9c88-469b-8e1d-384a28bb0006" in license_ids


def test_api_knowledge_authorities(api_client):
    """
    Verifies GET /knowledge/authorities returns Delaware divisions.
    """
    response = api_client.get("/knowledge/authorities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    auth_ids = {auth["id"] for auth in data}
    assert "8e8d89e5-9c88-469b-8e1d-384a28bb0002" in auth_ids
    assert "8e8d89e5-9c88-469b-8e1d-384a28bb0004" in auth_ids


def test_api_compliance_generate_plan_success(api_client):
    """
    Verifies POST /compliance/generate-plan evaluates correctly.
    """
    payload = {
        "business_type": "LLC",
        "state": "DE",
        "industry": "General Business",
        "employees": 5,
        "annual_revenue": 200000.0,
        "ownership_type": "LLC",
        "is_foreign_owner": False,
        "is_home_based": False,
        "additional_attributes": {}
    }
    response = api_client.post("/compliance/generate-plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "profile" in data
    assert "matched_rules" in data
    assert "eligibility_result" in data
    assert "workflow_result" in data
    assert data["eligibility_result"]["status"] == "ELIGIBLE"


def test_api_compliance_validation_errors(api_client):
    """
    Verifies POST /compliance/generate-plan rejects invalid payloads.
    """
    # Missing business_type, state, etc. should map to status 400 under global handlers
    payload = {
        "employees": 5
    }
    response = api_client.post("/compliance/generate-plan", json=payload)
    assert response.status_code == 400


def test_api_404_handling(api_client):
    """
    Verifies that requesting an unregistered path returns a 404.
    """
    response = api_client.get("/non-existent-endpoint")
    assert response.status_code == 404
