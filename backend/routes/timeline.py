"""
Timeline routes — Election process timeline and civic readiness endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.election_data import (
    ELECTION_STEPS,
    compute_readiness,
    get_full_timeline,
    get_step_by_id,
    get_step_by_phase,
)
from backend.models import ElectionPhase, ElectionType, ReadinessCheckRequest

router = APIRouter(prefix="/api/timeline", tags=["Timeline"])


@router.get("")
async def get_timeline(election_type: str = "general") -> dict[str, Any]:
    """Get the complete election process timeline."""
    try:
        etype = ElectionType(election_type)
    except ValueError:
        etype = ElectionType.GENERAL
    timeline = get_full_timeline(etype)
    return timeline.model_dump()


@router.get("/steps")
async def list_steps() -> list[dict[str, Any]]:
    """List all election process steps."""
    return [s.model_dump() for s in ELECTION_STEPS]


@router.get("/steps/{step_id}")
async def get_step(step_id: str) -> dict[str, Any]:
    """Get a specific election step by ID."""
    step = get_step_by_id(step_id)
    if not step:
        raise HTTPException(status_code=404, detail=f"Step not found: {step_id}")
    return step.model_dump()


@router.get("/phases/{phase}")
async def get_phase(phase: str) -> dict[str, Any]:
    """Get election step by phase name."""
    try:
        p = ElectionPhase(phase)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid phase: {phase}") from None
    step = get_step_by_phase(p)
    if not step:
        raise HTTPException(status_code=404, detail=f"Phase not found: {phase}")
    return step.model_dump()


@router.post("/readiness")
async def check_readiness(request: ReadinessCheckRequest) -> dict[str, Any]:
    """Assess a user's civic readiness to vote."""
    result = compute_readiness(request)
    return result.model_dump()
