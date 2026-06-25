import pytest
from backend.app.services.knowledge_loader import KnowledgeLoader
from backend.app.services.policy_loader import PolicyLoader
from backend.app.core.exceptions import KnowledgeLoadError, PolicyLoadError, ResourceNotFoundError


def test_knowledge_loader_success(temp_knowledge_dir):
    loader = KnowledgeLoader(knowledge_dir=temp_knowledge_dir)
    
    # Load valid file
    data = loader.load_file("businesses", "cafe.json")
    assert data["uuid"] == "test-uuid-12345"
    assert data["business_name"] == "Mock Cafe"

    # Verify category listing
    all_biz = loader.load_category("businesses")
    # Note: 'invalid_cafe.json' fails validation and is skipped in category loading
    assert len(all_biz) == 1
    assert all_biz[0]["business_name"] == "Mock Cafe"


def test_knowledge_loader_validation_failure(temp_knowledge_dir):
    loader = KnowledgeLoader(knowledge_dir=temp_knowledge_dir)
    
    # Try loading invalid file (missing business_name)
    with pytest.raises(KnowledgeLoadError) as exc_info:
        loader.load_file("businesses", "invalid_cafe.json")
    assert "validation failed" in str(exc_info.value).lower()


def test_knowledge_loader_missing_file(temp_knowledge_dir):
    loader = KnowledgeLoader(knowledge_dir=temp_knowledge_dir)
    
    with pytest.raises(ResourceNotFoundError):
        loader.load_file("businesses", "non_existent.json")


def test_policy_loader_success(temp_knowledge_dir):
    loader = PolicyLoader(knowledge_dir=temp_knowledge_dir)
    
    # Load valid rule
    data = loader.load_rule("rule_x.json")
    assert data["id"] == "rule-uuid-999"
    assert data["description"] == "Must do X"

    # Verify loading all
    all_rules = loader.load_all_rules()
    assert len(all_rules) == 1
    assert all_rules[0]["id"] == "rule-uuid-999"
