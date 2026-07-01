import os
import json
from typing import Dict, List, Optional, Any
from loguru import logger

from backend.app.core.config import settings
from backend.app.knowledge.models import KnowledgeObject, KnowledgeReference

TYPE_TO_DIR = {
    "license": "licenses",
    "authority": "authorities",
    "document": "documents",
    "timeline": "timelines",
    "fee": "fees",
    "rule": "rules",
    "business": "businesses",
    "notification": "notifications",
    "penalty": "penalties",
    "renewal": "renewals",
    "source": "sources",
    "act": "acts"
}


class KnowledgeRepository:
    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = knowledge_dir or settings.KNOWLEDGE_DIR
        self._cache: Dict[str, KnowledgeObject] = {}
        self._references: List[KnowledgeReference] = []

    def load_all(self) -> List[KnowledgeObject]:
        """
        Scans folders inside the knowledge directory and loads canonical knowledge objects.
        """
        if not os.path.exists(self.knowledge_dir):
            return []

        self._cache.clear()
        for root, dirs, files in os.walk(self.knowledge_dir):
            # Skip the schemas folder
            if "schemas" in root:
                continue
            for file in files:
                if file.endswith(".json") and file != "references.json":
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if isinstance(data, dict) and "id" in data and "type" in data:
                            obj = KnowledgeObject(**data)
                            self._cache[obj.id] = obj
                    except Exception as e:
                        logger.debug(f"Skipping non-canonical JSON {file_path}: {e}")
        return list(self._cache.values())

    def load_references(self) -> List[KnowledgeReference]:
        """
        Loads references from references.json inside the knowledge directory.
        """
        ref_path = os.path.join(self.knowledge_dir, "references.json")
        if not os.path.exists(ref_path):
            self._references = []
            return []

        try:
            with open(ref_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._references = [KnowledgeReference(**item) for item in data]
            else:
                self._references = []
        except Exception as e:
            logger.warning(f"Could not load references from {ref_path}: {e}")
            self._references = []
        return self._references

    def store(self, obj: KnowledgeObject) -> None:
        """
        Stores a knowledge object in the appropriate category subdirectory.
        """
        category = TYPE_TO_DIR.get(obj.type, obj.type + "s")
        target_dir = os.path.join(self.knowledge_dir, category)
        os.makedirs(target_dir, exist_ok=True)

        target_file = os.path.join(target_dir, f"{obj.id}.json")
        try:
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(obj.model_dump(), f, indent=2)
            self._cache[obj.id] = obj
            logger.info(f"Stored KnowledgeObject {obj.id} in {target_file}")
        except Exception as e:
            logger.error(f"Failed to store KnowledgeObject {obj.id}: {e}")
            raise

    def store_references(self, refs: List[KnowledgeReference]) -> None:
        """
        Saves the references list to references.json.
        """
        ref_path = os.path.join(self.knowledge_dir, "references.json")
        os.makedirs(self.knowledge_dir, exist_ok=True)
        try:
            with open(ref_path, "w", encoding="utf-8") as f:
                json.dump([ref.model_dump() for ref in refs], f, indent=2)
            self._references = refs.copy()
            logger.info(f"Stored {len(refs)} references in {ref_path}")
        except Exception as e:
            logger.error(f"Failed to store references: {e}")
            raise

    def update(self, obj: KnowledgeObject) -> None:
        """
        Updates an existing knowledge object.
        """
        self.store(obj)

    def lookup_by_id(self, obj_id: str) -> Optional[KnowledgeObject]:
        if not self._cache:
            self.load_all()
        return self._cache.get(obj_id)

    def lookup_by_type(self, obj_type: str) -> List[KnowledgeObject]:
        if not self._cache:
            self.load_all()
        return [obj for obj in self._cache.values() if obj.type == obj_type]

    def lookup_by_jurisdiction(self, jurisdiction: str) -> List[KnowledgeObject]:
        if not self._cache:
            self.load_all()
        return [obj for obj in self._cache.values() if obj.jurisdiction == jurisdiction]

    def lookup_by_authority(self, authority: str) -> List[KnowledgeObject]:
        if not self._cache:
            self.load_all()
        return [obj for obj in self._cache.values() if obj.authority == authority]
