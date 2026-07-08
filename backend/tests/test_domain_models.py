import pytest
from pydantic import ValidationError

from backend.app.domain import (
    Jurisdiction,
    Business,
    Authority,
    License,
    Permit,
    Fee,
    Deadline,
    Penalty,
    Tax,
    ComplianceTask,
)


def test_jurisdiction_model():
    # 1. Success with required fields
    jur = Jurisdiction(id="US", name="United States", level="Federal", country="US")
    assert jur.id == "US"
    assert jur.name == "United States"
    assert jur.level == "Federal"
    assert jur.country == "US"

    # 2. Validation error on missing field
    with pytest.raises(ValidationError):
        Jurisdiction(id="US", name="United States", level="Federal")

    # 3. Serialization
    data = jur.model_dump()
    assert data["id"] == "US"
    assert "name" in data


def test_business_model():
    biz = Business(
        id="biz-123",
        name="Main Street Food Kitchen",
        category="Food Service",
        type="LLC",
        jurisdiction_id="KA",
        primary_activity_code="NIC-47110"
    )
    assert biz.id == "biz-123"
    assert biz.name == "Main Street Food Kitchen"
    
    with pytest.raises(ValidationError):
        Business(id="biz-123", name="Fail Biz")


def test_authority_model():
    # Test with optional fields omitted
    auth1 = Authority(
        id="auth-99",
        name="State Liquor Board",
        jurisdiction_id="NY"
    )
    assert auth1.ministry_or_department is None
    assert auth1.official_website is None
    
    # Test with optional fields provided
    auth2 = Authority(
        id="auth-99",
        name="State Liquor Board",
        jurisdiction_id="NY",
        ministry_or_department="Department of State",
        official_website="https://liquor.ny.gov"
    )
    assert auth2.ministry_or_department == "Department of State"
    assert auth2.official_website == "https://liquor.ny.gov"


def test_license_model():
    lic = License(
        id="lic-001",
        title="FSSAI Food Vendor License",
        description="Mandatory food vendor license in India.",
        authority_id="auth-fssai",
        jurisdiction_id="IN",
        effective_date="2026-01-01",
        version="1.0.0",
        tags=["food", "retail"]
    )
    assert lic.id == "lic-001"
    assert lic.expiry_date is None
    assert lic.tags == ["food", "retail"]

    # Serialization check
    json_str = lic.model_dump_json()
    assert '"version":"1.0.0"' in json_str


def test_permit_model():
    permit = Permit(
        id="p-100",
        title="Outdoor Dining Permit",
        description="Permission to place dining tables on public sidewalk",
        authority_id="auth-blr-municipal",
        jurisdiction_id="KA",
        effective_date="2026-05-01"
    )
    assert permit.id == "p-100"
    assert permit.duration_days is None
    assert permit.expiry_date is None

    permit_with_expiry = Permit(
        id="p-100",
        title="Outdoor Dining Permit",
        description="Permission to place dining tables on public sidewalk",
        authority_id="auth-blr-municipal",
        jurisdiction_id="KA",
        duration_days=90,
        effective_date="2026-05-01",
        expiry_date="2026-08-01"
    )
    assert permit_with_expiry.duration_days == 90
    assert permit_with_expiry.expiry_date == "2026-08-01"


def test_fee_model():
    fee = Fee(
        id="fee-01",
        amount=5000.0,
        payment_mode="Online",
        frequency="annual",
        associated_object_id="lic-001"
    )
    assert fee.amount == 5000.0
    assert fee.currency == "INR" # default currency
    
    fee_usd = Fee(
        id="fee-02",
        amount=150.0,
        currency="USD",
        payment_mode="Demand Draft",
        frequency="one-time",
        associated_object_id="permit-123"
    )
    assert fee_usd.currency == "USD"
    assert fee_usd.amount == 150.0


def test_deadline_model():
    deadline = Deadline(
        id="dl-01",
        title="Quarterly Tax Filing",
        due_date="2026-06-30",
        associated_object_id="tax-rule-101"
    )
    assert deadline.due_date == "2026-06-30"
    assert deadline.recurring is False # default value

    recurring_dl = Deadline(
        id="dl-02",
        title="Annual License Renewal",
        due_date="Every Dec 31",
        recurring=True,
        associated_object_id="lic-001"
    )
    assert recurring_dl.recurring is True
    assert recurring_dl.due_date == "Every Dec 31"


def test_penalty_model():
    penalty = Penalty(
        id="pen-1",
        description="Failure to file GST",
        associated_object_id="dl-01"
    )
    assert penalty.flat_fee is None
    assert penalty.daily_rate is None
    assert penalty.severity == "medium" # default severity

    penalty_full = Penalty(
        id="pen-2",
        description="Unauthorized operation after license expiration",
        flat_fee=10000.0,
        daily_rate=500.0,
        max_cap=50000.0,
        severity="high",
        associated_object_id="lic-001"
    )
    assert penalty_full.flat_fee == 10000.0
    assert penalty_full.daily_rate == 500.0
    assert penalty_full.max_cap == 50000.0
    assert penalty_full.severity == "high"


def test_tax_model():
    tax = Tax(
        id="tax-gst",
        title="CGST Standard Rate",
        rate=0.09,
        type="GST",
        jurisdiction_id="IN"
    )
    assert tax.id == "tax-gst"
    assert tax.rate == 0.09
    assert tax.type == "GST"
    
    with pytest.raises(ValidationError):
        Tax(id="tax-gst", title="GST", rate=9.0) # type missing


def test_compliance_task_model():
    task = ComplianceTask(
        id="task-01",
        title="FSSAI Registration Submission",
        description="Fill and submit Form A on the FSSAI online portal.",
        associated_object_id="lic-001"
    )
    assert task.status == "pending" # default status
    assert task.due_date is None

    task_completed = ComplianceTask(
        id="task-02",
        title="Pay Licensing Fee",
        description="Complete online challan transaction of 5000 INR.",
        due_date="2026-05-15",
        status="completed",
        associated_object_id="fee-01"
    )
    assert task_completed.status == "completed"
    assert task_completed.due_date == "2026-05-15"
