from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


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
