import os
import json
from typing import Dict, Any, List, Optional
from jsonschema import validate, ValidationError
from loguru import logger
from backend.app.core.config import settings
from backend.app.core.exceptions import PolicyLoadError, ResourceNotFoundError


class PolicyLoader:
    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = knowledge_dir or settings.KNOWLEDGE_DIR
        self._schema_cache: Optional[Dict[str, Any]] = None
        self._rules_cache: Dict[str, Dict[str, Any]] = {}  # Key: rule filename, Value: rule dict

    def load_rule_schema(self) -> Dict[str, Any]:
        """Loads and caches the policy rule JSON Schema."""
        if self._schema_cache:
            return self._schema_cache

        schema_path = os.path.join(self.knowledge_dir, "schemas", "policy_rule.schema.json")
        if not os.path.exists(schema_path):
            raise ResourceNotFoundError(f"Policy rule schema file not found at path: {schema_path}")

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            self._schema_cache = schema_data
            logger.info("Loaded and cached policy rule schema.")
            return schema_data
        except Exception as e:
            raise PolicyLoadError(f"Failed to load policy rule schema: {str(e)}")

    def load_rule(self, filename: str) -> Dict[str, Any]:
        """Loads, validates, and caches a specific policy rule JSON file."""
        if filename in self._rules_cache:
            return self._rules_cache[filename]

        file_path = os.path.join(self.knowledge_dir, "rules", filename)
        if not os.path.exists(file_path):
            raise ResourceNotFoundError(f"Policy rule file not found at path: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise PolicyLoadError(f"Failed to parse policy rule JSON file {filename}: {str(e)}")

        # Validate against schema
        schema = self.load_rule_schema()
        try:
            validate(instance=data, schema=schema)
            logger.debug(f"Validated rule {filename} successfully against policy_rule.schema.json")
        except ValidationError as ve:
            raise PolicyLoadError(
                message=f"JSON validation failed for policy rule {filename}",
                details={"error": ve.message, "path": list(ve.path)}
            )

        self._rules_cache[filename] = data
        return data

    def load_all_rules(self) -> List[Dict[str, Any]]:
        """Loads and returns all valid policy rules inside data/knowledge/rules/ directory."""
        rules_dir = os.path.join(self.knowledge_dir, "rules")
        if not os.path.exists(rules_dir):
            return []

        results = []
        for filename in os.listdir(rules_dir):
            if filename.endswith(".json"):
                try:
                    data = self.load_rule(filename)
                    results.append(data)
                except Exception as e:
                    logger.error(f"Skipping malformed rule file {filename}: {str(e)}")
                    continue
        return results

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Finds a loaded policy rule by its ID property."""
        rules = self.load_all_rules()
        for rule in rules:
            if rule.get("id") == rule_id:
                return rule
        return None

    def clear_cache(self) -> None:
        """Clears all cached rules and schemas."""
        self._schema_cache = None
        self._rules_cache.clear()
        logger.info("Cleared PolicyLoader memory caches.")
