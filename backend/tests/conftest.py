import os
import tempfile
import json
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.app.core.config import Settings
from backend.app.core.dependencies import get_settings


@pytest.fixture
def temp_knowledge_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create folder structure
        os.makedirs(os.path.join(tmpdir, "schemas"))
        os.makedirs(os.path.join(tmpdir, "businesses"))
        os.makedirs(os.path.join(tmpdir, "rules"))

        # Create a mock business schema
        mock_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "uuid": { "type": "string" },
                "business_name": { "type": "string" }
            },
            "required": ["uuid", "business_name"]
        }
        with open(os.path.join(tmpdir, "schemas", "business.schema.json"), "w") as f:
            json.dump(mock_schema, f)

        # Create a mock policy rule schema
        mock_rule_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "id": { "type": "string" },
                "description": { "type": "string" }
            },
            "required": ["id", "description"]
        }
        with open(os.path.join(tmpdir, "schemas", "policy_rule.schema.json"), "w") as f:
            json.dump(mock_rule_schema, f)

        # Create a valid mock business config
        mock_business = {
            "uuid": "test-uuid-12345",
            "business_name": "Mock Cafe"
        }
        with open(os.path.join(tmpdir, "businesses", "cafe.json"), "w") as f:
            json.dump(mock_business, f)

        # Create an invalid mock business config (missing required business_name)
        mock_invalid_business = {
            "uuid": "test-uuid-12345"
        }
        with open(os.path.join(tmpdir, "businesses", "invalid_cafe.json"), "w") as f:
            json.dump(mock_invalid_business, f)

        # Create a valid mock policy rule
        mock_rule = {
            "id": "rule-uuid-999",
            "description": "Must do X"
        }
        with open(os.path.join(tmpdir, "rules", "rule_x.json"), "w") as f:
            json.dump(mock_rule, f)

        yield tmpdir


@pytest.fixture
def test_app(temp_knowledge_dir):
    # Override settings for testing
    test_settings = Settings(
        ENV="testing",
        KNOWLEDGE_DIR=temp_knowledge_dir
    )

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    
    # We must also patch the settings in core/dependencies.py if needed, 
    # but for simple unit tests, overrides work perfectly.
    yield app


@pytest.fixture
def client(test_app):
    with TestClient(test_app) as client:
        yield client
