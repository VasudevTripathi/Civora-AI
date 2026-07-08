from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field
from backend.app.decision.models import (
    BusinessProfile,
    ApplicableRule,
    EvaluationResult,
    DependencyGraph,
    EligibilityResult,
    WorkflowResult,
)


class CompliancePlan(BaseModel):
    profile: BusinessProfile
    matched_rules: List[ApplicableRule]
    evaluation_result: EvaluationResult
    dependency_graph: DependencyGraph
    eligibility_result: EligibilityResult
    workflow_result: WorkflowResult
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0.0"
