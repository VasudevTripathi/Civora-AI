from typing import List
from fastapi import APIRouter, Depends

from backend.app.knowledge.repository import KnowledgeRepository
from backend.app.knowledge.models import KnowledgeObject
from backend.app.core.dependencies import get_knowledge_repository

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.get("/businesses", response_model=List[KnowledgeObject])
async def get_businesses(
    repo: KnowledgeRepository = Depends(get_knowledge_repository)
) -> List[KnowledgeObject]:
    """
    Retrieves all business formation profiles stored in the knowledge base.
    """
    return repo.lookup_by_type("business")


@router.get("/licenses", response_model=List[KnowledgeObject])
async def get_licenses(
    repo: KnowledgeRepository = Depends(get_knowledge_repository)
) -> List[KnowledgeObject]:
    """
    Retrieves all licenses stored in the knowledge base.
    """
    return repo.lookup_by_type("license")


@router.get("/authorities", response_model=List[KnowledgeObject])
async def get_authorities(
    repo: KnowledgeRepository = Depends(get_knowledge_repository)
) -> List[KnowledgeObject]:
    """
    Retrieves all authorities stored in the knowledge base.
    """
    return repo.lookup_by_type("authority")
