import time
from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from backend.app.core.exceptions import AppException, PolicyLoadError
from backend.app.services.policy_loader import PolicyLoader
from backend.app.services.knowledge_loader import KnowledgeLoader
from backend.app.decision.engine import RuleEngine
from backend.app.decision.evaluator import ConditionEvaluator
from backend.app.decision.dependency import DependencyResolver
from backend.app.decision.eligibility import EligibilityEngine
from backend.app.decision.workflow import WorkflowEngine
from backend.app.decision.models import BusinessProfile
from backend.app.compliance.models import CompliancePlan


class ComplianceEngine:
    """
    ComplianceEngine acts as a Facade over the Civora decision-layer engines.
    It coordinates the end-to-end compliance evaluation pipeline.
    """
    def __init__(
        self,
        knowledge_dir: Optional[str] = None,
        policy_loader: Optional[PolicyLoader] = None,
        knowledge_loader: Optional[KnowledgeLoader] = None,
        rule_engine: Optional[RuleEngine] = None,
        evaluator: Optional[ConditionEvaluator] = None,
        resolver: Optional[DependencyResolver] = None,
        eligibility_engine: Optional[EligibilityEngine] = None,
        workflow_engine: Optional[WorkflowEngine] = None,
    ):
        self.knowledge_dir = knowledge_dir
        
        # Loaders
        self.policy_loader = policy_loader or PolicyLoader(knowledge_dir=self.knowledge_dir)
        self.knowledge_loader = knowledge_loader or KnowledgeLoader(knowledge_dir=self.knowledge_dir)
        
        # Decoupled Engines
        self.rule_engine = rule_engine or RuleEngine(policy_loader=self.policy_loader)
        self.evaluator = evaluator or ConditionEvaluator(policy_loader=self.policy_loader)
        self.resolver = resolver or DependencyResolver()
        self.eligibility_engine = eligibility_engine or EligibilityEngine(policy_loader=self.policy_loader)
        self.workflow_engine = workflow_engine or WorkflowEngine(
            policy_loader=self.policy_loader,
            knowledge_loader=self.knowledge_loader
        )

    def generate_plan(self, profile: BusinessProfile) -> CompliancePlan:
        """
        Runs the full compliance evaluation pipeline for the given business profile.
        """
        start_time = time.perf_counter()
        logger.info("Compliance pipeline started.")

        try:
            # Stage 1: Load Knowledge/Rules
            try:
                self.rule_engine.load_rules()
            except Exception as e:
                logger.error(f"Stage 1 Failure (Rule Loading): {e}")
                if isinstance(e, AppException):
                    raise
                raise PolicyLoadError(f"Failed to load rules: {str(e)}") from e

            # Stage 2: Rule matching
            try:
                rule_result = self.rule_engine.match(profile)
            except Exception as e:
                logger.error(f"Stage 2 Failure (Rule Matching): {e}")
                if isinstance(e, AppException):
                    raise
                raise AppException(f"Rule matching failed: {str(e)}") from e

            # Stage 3: Condition Evaluation
            try:
                evaluation_result = self.evaluator.evaluate(profile, rule_result.matched_rules)
            except Exception as e:
                logger.error(f"Stage 3 Failure (Condition Evaluation): {e}")
                if isinstance(e, AppException):
                    raise
                raise AppException(f"Condition evaluation failed: {str(e)}") from e

            # Stage 4: Dependency Resolution
            try:
                dependency_graph = self.resolver.build_graph(
                    rule_result.matched_rules,
                    evaluation_result.evaluations
                )
            except Exception as e:
                logger.error(f"Stage 4 Failure (Dependency Resolution): {e}")
                if isinstance(e, AppException):
                    raise
                raise AppException(f"Dependency resolution failed: {str(e)}") from e

            # Stage 5: Eligibility Checks
            try:
                eligibility_result = self.eligibility_engine.evaluate(
                    profile,
                    rule_result.matched_rules,
                    evaluation_result,
                    dependency_graph
                )
            except Exception as e:
                logger.error(f"Stage 5 Failure (Eligibility Checks): {e}")
                if isinstance(e, AppException):
                    raise
                raise AppException(f"Eligibility checks failed: {str(e)}") from e

            # Stage 6: Workflow Generation
            try:
                workflow_result = self.workflow_engine.generate(
                    profile,
                    rule_result,
                    evaluation_result,
                    dependency_graph,
                    eligibility_result
                )
            except Exception as e:
                logger.error(f"Stage 6 Failure (Workflow Generation): {e}")
                if isinstance(e, AppException):
                    raise
                raise AppException(f"Workflow generation failed: {str(e)}") from e

            # Stage 7: Return CompliancePlan
            plan = CompliancePlan(
                profile=profile,
                matched_rules=rule_result.matched_rules,
                evaluation_result=evaluation_result,
                dependency_graph=dependency_graph,
                eligibility_result=eligibility_result,
                workflow_result=workflow_result,
                generated_at=datetime.now(timezone.utc),
                version="1.0.0"
            )

            elapsed_time = time.perf_counter() - start_time
            logger.info(f"Compliance pipeline completed successfully in {elapsed_time:.4f} seconds.")
            return plan

        except Exception as e:
            elapsed_time = time.perf_counter() - start_time
            logger.error(f"Compliance pipeline aborted after {elapsed_time:.4f} seconds.")
            raise
