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
