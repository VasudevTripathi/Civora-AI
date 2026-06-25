import os
import json
from typing import Dict, Any, List, Optional
from jsonschema import validate, ValidationError
from loguru import logger
from backend.app.core.config import settings
from backend.app.core.exceptions import KnowledgeLoadError, ResourceNotFoundError


class KnowledgeLoader:
    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = knowledge_dir or settings.KNOWLEDGE_DIR
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self._knowledge_cache: Dict[str, Dict[str, Any]] = {}  # Key: "category/filename.json", Value: parsed dict

    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """Loads and caches a JSON schema by name (e.g., 'business.schema.json')"""
        if schema_name in self._schema_cache:
            return self._schema_cache[schema_name]

        schema_path = os.path.join(self.knowledge_dir, "schemas", schema_name)
        if not os.path.exists(schema_path):
            raise ResourceNotFoundError(f"Schema file not found at path: {schema_path}")

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            self._schema_cache[schema_name] = schema_data
            logger.info(f"Loaded and cached schema: {schema_name}")
            return schema_data
        except Exception as e:
            raise KnowledgeLoadError(f"Failed to load schema {schema_name}: {str(e)}")

    def load_file(self, category: str, filename: str) -> Dict[str, Any]:
        """Loads, validates, and caches a specific JSON compliance node file."""
        cache_key = f"{category}/{filename}"
        if cache_key in self._knowledge_cache:
            return self._knowledge_cache[cache_key]

        file_path = os.path.join(self.knowledge_dir, category, filename)
        if not os.path.exists(file_path):
            raise ResourceNotFoundError(f"Knowledge file not found at path: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise KnowledgeLoadError(f"Failed to parse JSON file {filename}: {str(e)}")

        # Map folder category to validation schema file name
        # If folder is 'businesses', validate against 'business.schema.json'
        # Remove trailing 's' if exists, or do mapping
        schema_mapping = {
            "businesses": "business.schema.json",
            "licenses": "license.schema.json",
            "authorities": "authority.schema.json",
            "acts": "legal_act.schema.json",
            "rules": "rule.schema.json",
            "fees": "fee.schema.json",
            "documents": "document.schema.json",
            "timelines": "timeline.schema.json",
            "renewals": "renewal.schema.json",
            "penalties": "penalty.schema.json",
            "notifications": "notification.schema.json",
            "sources": "source.schema.json",
        }

        schema_name = schema_mapping.get(category)
        if schema_name:
            schema = self.load_schema(schema_name)
            try:
                validate(instance=data, schema=schema)
                logger.debug(f"Validated {filename} successfully against {schema_name}")
            except ValidationError as ve:
                raise KnowledgeLoadError(
                    message=f"JSON validation failed for {filename} against {schema_name}",
                    details={"error": ve.message, "path": list(ve.path)}
                )

        self._knowledge_cache[cache_key] = data
        return data

    def load_category(self, category: str) -> List[Dict[str, Any]]:
        """Loads and returns all valid JSON configurations inside a directory category."""
        category_dir = os.path.join(self.knowledge_dir, category)
        if not os.path.exists(category_dir):
            return []

        results = []
        for filename in os.listdir(category_dir):
            if filename.endswith(".json"):
                try:
                    data = self.load_file(category, filename)
                    results.append(data)
                except Exception as e:
                    logger.error(f"Skipping malformed file {filename} in {category}: {str(e)}")
                    continue
        return results

    def get_by_uuid(self, category: str, uuid: str) -> Optional[Dict[str, Any]]:
        """Finds a loaded knowledge object by its UUID property."""
        items = self.load_category(category)
        for item in items:
            if item.get("uuid") == uuid:
                return item
        return None

    def clear_cache(self) -> None:
        """Clears all cached schemas and data nodes."""
        self._schema_cache.clear()
        self._knowledge_cache.clear()
        logger.info("Cleared KnowledgeLoader memory caches.")
