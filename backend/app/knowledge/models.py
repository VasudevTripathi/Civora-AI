from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class KnowledgeObject(BaseModel):
    id: str
    type: str
    jurisdiction: str
    authority: str
    title: str
    description: str
    effective_date: str
    expiry_date: Optional[str] = None
    version: str
    source: str
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeReference(BaseModel):
    from_id: str
    to_id: str
    relationship: str
