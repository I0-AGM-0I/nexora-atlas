"""
NEXORA ATLAS - Demo Management API Endpoints
Guarded strictly by settings.DEMO_MODE.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.demo import seed_demo_data, reset_demo_data, validate_demo_dataset

router = APIRouter(prefix="/demo", tags=["Demo Environment"])


def require_demo_mode():
    """Security guardrail ensuring demo endpoints are never callable in live production."""
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo environment management endpoints are disabled when DEMO_MODE is false.",
        )


@router.get("/status", dependencies=[Depends(require_demo_mode)], summary="Check demo dataset health and metrics")
async def get_demo_status(session: AsyncSession = Depends(get_db)):
    try:
        report = await validate_demo_dataset(session)
        return {"status": "active", "health": report}
    except Exception as e:
        return {"status": "unseeded_or_error", "detail": str(e)}


@router.post("/seed", dependencies=[Depends(require_demo_mode)], summary="Trigger deterministic demo dataset seed")
async def trigger_demo_seed(session: AsyncSession = Depends(get_db)):
    result = await seed_demo_data(session, reset_first=True)
    return {"message": "Demo environment seeded successfully.", "details": result}


@router.post("/reset", dependencies=[Depends(require_demo_mode)], summary="Reset demo dataset")
async def trigger_demo_reset(session: AsyncSession = Depends(get_db)):
    result = await reset_demo_data(session)
    return {"message": "Demo dataset reset successfully.", "details": result}
