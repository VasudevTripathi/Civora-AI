from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum


class BusinessProfile(BaseModel):
    business_type: str
    state: str
    county: Optional[str] = None
    city: Optional[str] = None
    industry: str
    employees: int
    annual_revenue: float
    ownership_type: str
    is_foreign_owner: bool
    is_home_based: bool
    additional_attributes: Dict[str, Any] = Field(default_factory=dict)


class ApplicableRule(BaseModel):
    rule_id: str
    title: str
    description: str
    category: str
    authority: str
    priority: int
    dependencies: List[str] = Field(default_factory=list)
    source: str


class RuleEngineResult(BaseModel):
    profile: BusinessProfile
    matched_rules: List[ApplicableRule] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)


class ConditionStatus(str, Enum):
    SATISFIED = "SATISFIED"
    FAILED = "FAILED"
    PENDING_INFORMATION = "PENDING_INFORMATION"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ConditionEvaluation(BaseModel):
    rule_id: str
    status: ConditionStatus
    reason: str
    missing_fields: List[str] = Field(default_factory=list)
    evaluated_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvaluationResult(BaseModel):
    profile: BusinessProfile
    evaluations: List[ConditionEvaluation] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=dict)


class DependencyNode(BaseModel):
    rule_id: str
    title: str
    parents: List[str] = Field(default_factory=list)
    children: List[str] = Field(default_factory=list)
    depth: int = 0
    status: Optional[str] = None


class DependencyGraph(BaseModel):
    nodes: Dict[str, DependencyNode] = Field(default_factory=dict)
    roots: List[str] = Field(default_factory=list)
    leaf_nodes: List[str] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    cycles_detected: bool = False


class EligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    CONDITIONALLY_ELIGIBLE = "CONDITIONALLY_ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


class EligibilityIssue(BaseModel):
    rule_id: str
    severity: str  # ERROR, WARNING, INFO
    message: str
    blocking: bool
    recommended_action: str


class EligibilityResult(BaseModel):
    status: EligibilityStatus
    issues: List[EligibilityIssue] = Field(default_factory=list)
    blocking_rules: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    AVAILABLE = "AVAILABLE"
    BLOCKED = "BLOCKED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class WorkflowStep(BaseModel):
    step_id: str
    rule_id: str
    title: str
    description: str
    status: WorkflowStatus
    authority: str
    priority: int
    dependencies: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    estimated_duration: Optional[str] = None
    blocking_reason: Optional[str] = None


class WorkflowResult(BaseModel):
    steps: Dict[str, WorkflowStep] = Field(default_factory=dict)
    execution_order: List[str] = Field(default_factory=list)
    critical_path: List[str] = Field(default_factory=list)
    blocked_steps: List[str] = Field(default_factory=list)
    completion_percentage: float = 0.0
    summary: Dict[str, Any] = Field(default_factory=dict)
