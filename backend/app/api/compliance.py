from fastapi import APIRouter, Depends

from backend.app.compliance.engine import ComplianceEngine
from backend.app.compliance.models import CompliancePlan
from backend.app.decision.models import BusinessProfile
from backend.app.core.dependencies import get_compliance_engine

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.post("/generate-plan", response_model=CompliancePlan)
async def generate_plan(
    profile: BusinessProfile,
    engine: ComplianceEngine = Depends(get_compliance_engine)
) -> CompliancePlan:
    """
    Evaluates a business profile and generates a structured compliance plan.
    """
    return engine.generate_plan(profile)
