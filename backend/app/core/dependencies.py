from backend.app.services.knowledge_loader import KnowledgeLoader
from backend.app.services.policy_loader import PolicyLoader
from backend.app.core.config import settings

# Import decision layer and compliance engines
from backend.app.decision.engine import RuleEngine
from backend.app.decision.evaluator import ConditionEvaluator
from backend.app.decision.dependency import DependencyResolver
from backend.app.decision.eligibility import EligibilityEngine
from backend.app.decision.workflow import WorkflowEngine
from backend.app.compliance.engine import ComplianceEngine
from backend.app.knowledge.repository import KnowledgeRepository

# Global Singletons
_knowledge_loader = KnowledgeLoader(knowledge_dir=settings.KNOWLEDGE_DIR)
_policy_loader = PolicyLoader(knowledge_dir=settings.KNOWLEDGE_DIR)
_knowledge_repository = KnowledgeRepository(knowledge_dir=settings.KNOWLEDGE_DIR)

# Instantiate engines with dependency injection
_rule_engine = RuleEngine(policy_loader=_policy_loader)
_evaluator = ConditionEvaluator(policy_loader=_policy_loader)
_resolver = DependencyResolver()
_eligibility_engine = EligibilityEngine(policy_loader=_policy_loader)
_workflow_engine = WorkflowEngine(
    policy_loader=_policy_loader,
    knowledge_loader=_knowledge_loader
)
_compliance_engine = ComplianceEngine(
    policy_loader=_policy_loader,
    knowledge_loader=_knowledge_loader,
    rule_engine=_rule_engine,
    evaluator=_evaluator,
    resolver=_resolver,
    eligibility_engine=_eligibility_engine,
    workflow_engine=_workflow_engine,
)


def get_settings():
    """Returns application configuration settings."""
    return settings


def get_knowledge_loader() -> KnowledgeLoader:
    """Returns the global KnowledgeLoader singleton instance."""
    return _knowledge_loader


def get_policy_loader() -> PolicyLoader:
    """Returns the global PolicyLoader singleton instance."""
    return _policy_loader


def get_rule_engine() -> RuleEngine:
    """Returns the rule engine singleton instance."""
    return _rule_engine


def get_condition_evaluator() -> ConditionEvaluator:
    """Returns the condition evaluator singleton instance."""
    return _evaluator


def get_dependency_resolver() -> DependencyResolver:
    """Returns the dependency resolver singleton instance."""
    return _resolver


def get_eligibility_engine() -> EligibilityEngine:
    """Returns the eligibility engine singleton instance."""
    return _eligibility_engine


def get_workflow_engine() -> WorkflowEngine:
    """Returns the workflow engine singleton instance."""
    return _workflow_engine


def get_compliance_engine() -> ComplianceEngine:
    """Returns the compliance engine singleton instance."""
    return _compliance_engine


def get_knowledge_repository() -> KnowledgeRepository:
    """Returns the global KnowledgeRepository singleton instance."""
    return _knowledge_repository
