from backend.app.services.knowledge_loader import KnowledgeLoader
from backend.app.services.policy_loader import PolicyLoader
from backend.app.core.config import settings

# Global Singletons
_knowledge_loader = KnowledgeLoader(knowledge_dir=settings.KNOWLEDGE_DIR)
_policy_loader = PolicyLoader(knowledge_dir=settings.KNOWLEDGE_DIR)


def get_settings():
    """Returns application configuration settings."""
    return settings


def get_knowledge_loader() -> KnowledgeLoader:
    """Returns the global KnowledgeLoader singleton instance."""
    return _knowledge_loader


def get_policy_loader() -> PolicyLoader:
    """Returns the global PolicyLoader singleton instance."""
    return _policy_loader
