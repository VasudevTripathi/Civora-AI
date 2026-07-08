from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Jurisdiction(BaseModel):
    """
    Defines the geopolitical or administrative region where a regulation applies.
    """
    id: str = Field(description="Unique code/identifier for the jurisdiction (e.g., US, KA, NY)")
    name: str = Field(description="Display/regulatory name of the jurisdiction")
    level: str = Field(description="Level: Federal, State, Municipal, Local")
    country: str = Field(description="ISO or canonical country identifier")


class Business(BaseModel):
    """
    Represents the business profile seeking compliance evaluation.
    """
    id: str = Field(description="Unique business identifier")
    name: str = Field(description="Legal name of the business entity")
    category: str = Field(description="Business industry category (e.g., Food Service, Education)")
    type: str = Field(description="Legal registration type (e.g., LLC, Private Limited, Partnership)")
    jurisdiction_id: str = Field(description="Foreign key ID referencing the home Jurisdiction")
    primary_activity_code: str = Field(description="Standard classification code (e.g. NIC-47110)")


class Authority(BaseModel):
    """
    Represents a governing regulatory agency or administrative body.
    """
    id: str = Field(description="Unique authority identifier")
    name: str = Field(description="Name of the government regulatory authority")
    jurisdiction_id: str = Field(description="Foreign key ID referencing the governed Jurisdiction")
    ministry_or_department: Optional[str] = Field(None, description="Parent administrative ministry or department")
    official_website: Optional[str] = Field(None, description="Official website URL link")


class License(BaseModel):
    """
    A legal authorization or license required for operating.
    """
    id: str = Field(description="Unique license identifier")
    title: str = Field(description="Official name of the license")
    description: str = Field(description="Detailed scope of the license")
    authority_id: str = Field(description="Foreign key ID referencing the issuing Authority")
    jurisdiction_id: str = Field(description="Foreign key ID referencing the governing Jurisdiction")
    effective_date: str = Field(description="Starting date when the license rule became active (YYYY-MM-DD)")
    expiry_date: Optional[str] = Field(None, description="Optional expiry date of the licensing rule (YYYY-MM-DD)")
    version: str = Field(description="Semantic version of this model representation")
    tags: List[str] = Field(default_factory=list, description="Descriptive classification tags")


class Permit(BaseModel):
    """
    An operational permission, certificate, or clearance (often site-specific or conditional).
    """
    id: str = Field(description="Unique permit identifier")
    title: str = Field(description="Official name of the permit")
    description: str = Field(description="Detail of permit operational requirements")
    authority_id: str = Field(description="Foreign key ID referencing the issuing Authority")
    jurisdiction_id: str = Field(description="Foreign key ID referencing the governing Jurisdiction")
    duration_days: Optional[int] = Field(None, description="Validity span of the permit in days once issued")
    effective_date: str = Field(description="Active date (YYYY-MM-DD)")
    expiry_date: Optional[str] = Field(None, description="Expiry date of permit rule (YYYY-MM-DD)")


class Fee(BaseModel):
    """
    Associated compliance costs for processing, registration, or penalty.
    """
    id: str = Field(description="Unique fee identifier")
    amount: float = Field(description="Fee amount value")
    currency: str = Field("INR", description="Three-letter currency code (default: INR)")
    payment_mode: str = Field(description="Supported modes: Online, Challan, Demand Draft, Free")
    frequency: str = Field(description="Fee billing cycle: one-time, annual, monthly, renewal")
    associated_object_id: str = Field(description="ID of the license, permit, or task this fee attaches to")


class Deadline(BaseModel):
    """
    Critical target dates for document submission, tax filing, or renewal.
    """
    id: str = Field(description="Unique deadline identifier")
    title: str = Field(description="Title of the target deadline task")
    due_date: str = Field(description="Target date in YYYY-MM-DD or a relative calculation instruction string")
    recurring: bool = Field(False, description="Whether the deadline repeats periodically")
    associated_object_id: str = Field(description="ID of the target license, permit, or compliance task")


class Penalty(BaseModel):
    """
    Consequences of non-compliance (e.g. fines, daily interest, max caps).
    """
    id: str = Field(description="Unique penalty identifier")
    description: str = Field(description="Detailed reason or regulatory code section for the penalty")
    flat_fee: Optional[float] = Field(None, description="One-off static penalty fee amount")
    daily_rate: Optional[float] = Field(None, description="Accrued daily fine rate for ongoing non-compliance")
    max_cap: Optional[float] = Field(None, description="Maximum ceiling cap of the penalty fee")
    severity: str = Field("medium", description="Severity level rating: low, medium, high")
    associated_object_id: str = Field(description="ID of the related license, permit, or deadline")


class Tax(BaseModel):
    """
    Tax rates, levies, or percentages governing business operations in a jurisdiction.
    """
    id: str = Field(description="Unique tax identifier")
    title: str = Field(description="Official name of the tax rule")
    rate: float = Field(description="Tax rate percentage or fractional multiplier")
    type: str = Field(description="Type: GST, VAT, Income, Sales, Excise")
    jurisdiction_id: str = Field(description="Foreign key ID referencing the governing Jurisdiction")


class ComplianceTask(BaseModel):
    """
    An actionable work item to resolve or maintain a compliance state.
    """
    id: str = Field(description="Unique compliance task identifier")
    title: str = Field(description="Short title of the task")
    description: str = Field(description="Actionable guide/steps needed to complete the task")
    due_date: Optional[str] = Field(None, description="Optional due date (YYYY-MM-DD)")
    status: str = Field("pending", description="Current status: pending, completed, overdue")
    associated_object_id: str = Field(description="ID of the corresponding license, permit, fee, or deadline")
