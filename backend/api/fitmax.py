"""
Fitmax API - profile, planning, tracking, and dashboard endpoints.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from middleware.auth_middleware import require_paid_user
from models.fitmax import (
    FitmaxProfileInput,
    WorkoutSessionLogRequest,
    NutritionLogRequest,
    MeasurementLogRequest,
)
from services.fitmax_service import fitmax_service


router = APIRouter(prefix="/fitmax", tags=["Fitmax"])


@router.get("/profile")
async def get_fitmax_profile(
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await fitmax_service.get_profile_response(current_user["id"], db)
    if not profile:
        return {"profile": None, "message": "Fitmax profile not set"}
    return {"profile": profile.model_dump()}


@router.post("/profile")
async def upsert_fitmax_profile(
    data: FitmaxProfileInput,
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await fitmax_service.upsert_profile(current_user["id"], data, db)
    await fitmax_service.seed_welcome_message_if_needed(current_user["id"], db)
    return {"profile": profile.model_dump()}


@router.put("/profile")
async def update_fitmax_profile(
    data: FitmaxProfileInput,
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await fitmax_service.upsert_profile(current_user["id"], data, db)
    return {"profile": profile.model_dump()}


@router.get("/dashboard")
async def get_fitmax_dashboard(
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dashboard = await fitmax_service.build_dashboard(current_user["id"], db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return dashboard


@router.get("/course/modules")
async def get_fitmax_course_modules(
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    modules = await fitmax_service.get_personalized_modules(current_user["id"], db)
    return {"modules": modules}


@router.get("/workout-plan")
async def get_fitmax_workout_plan(
    week: int = Query(default=1, ge=1, le=52),
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        plan = await fitmax_service.get_week_plan(current_user["id"], db, week_number=week)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"plan": plan.model_dump()}


@router.post("/workout/log")
async def log_fitmax_workout(
    payload: WorkoutSessionLogRequest,
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    result = await fitmax_service.log_workout(current_user["id"], payload, db)
    return {"result": result}


@router.post("/nutrition/log")
async def log_fitmax_nutrition(
    payload: NutritionLogRequest,
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    result = await fitmax_service.log_nutrition(current_user["id"], payload, db)
    return {"result": result}


@router.get("/nutrition/day")
async def get_fitmax_nutrition_day(
    day: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    parsed_day: Optional[date] = None
    if day:
        try:
            parsed_day = datetime.strptime(day, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid day format. Use YYYY-MM-DD")
    summary = await fitmax_service.get_daily_nutrition(current_user["id"], db, day=parsed_day)
    return summary


@router.post("/progress/measurements")
async def log_fitmax_measurements(
    payload: MeasurementLogRequest,
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    result = await fitmax_service.log_measurements(current_user["id"], payload, db)
    return {"result": result}


@router.get("/progress/overview")
async def get_fitmax_progress(
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    return await fitmax_service.get_progress_overview(current_user["id"], db)


@router.post("/coach/refresh-schedule")
async def refresh_fitmax_schedule(
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    await fitmax_service.refresh_fitmax_schedule(current_user["id"], db)
    return {"status": "ok"}

