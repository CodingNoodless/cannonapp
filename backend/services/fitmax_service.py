"""
Fitmax domain service.

This service owns:
- Fitness profile (single source of truth)
- Target calculators (TDEE, calories, macros)
- Rule-based workout plan generation
- Course module personalization
- Coach week-state tracking
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.fitmax import (
    FitGoalType,
    FitmaxProfileInput,
    FitmaxProfileResponse,
    FitmaxTargets,
    WorkoutExercise,
    WorkoutSessionPlan,
    WorkoutWeekPlan,
    NutritionLogRequest,
    MeasurementLogRequest,
    WorkoutSessionLogRequest,
)
from models.sqlalchemy_models import (
    User,
    UserSchedule,
    ChatHistory,
    FitmaxProfile,
    FitmaxWorkoutLog,
    FitmaxNutritionLog,
    FitmaxMeasurementLog,
    FitmaxWeekState,
)
from services.fitmax_content import build_fitmax_course_modules


ACTIVITY_MULTIPLIER = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
}


@dataclass
class SplitDay:
    day_label: str
    focus: str
    training: bool


def _parse_hhmm(value: Optional[str], fallback: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return fallback
    parts = raw.split(":")
    if len(parts) != 2:
        return fallback
    try:
        h = int(parts[0])
        m = int(parts[1])
    except ValueError:
        return fallback
    if h < 0 or h > 23 or m < 0 or m > 59:
        return fallback
    return f"{h:02d}:{m:02d}"


def _build_split(days_per_week: int, goal: str) -> List[SplitDay]:
    if days_per_week <= 3:
        base = [
            SplitDay("Mon", "Full Body A", True),
            SplitDay("Tue", "Recovery", False),
            SplitDay("Wed", "Full Body B", True),
            SplitDay("Thu", "Recovery", False),
            SplitDay("Fri", "Full Body C", True if days_per_week == 3 else False),
            SplitDay("Sat", "Recovery", False),
            SplitDay("Sun", "Recovery", False),
        ]
        if days_per_week == 2:
            base[4] = SplitDay("Fri", "Recovery", False)
        return base

    if days_per_week == 4:
        return [
            SplitDay("Mon", "Upper 1", True),
            SplitDay("Tue", "Lower 1", True),
            SplitDay("Wed", "Recovery", False),
            SplitDay("Thu", "Upper 2", True),
            SplitDay("Fri", "Lower 2", True),
            SplitDay("Sat", "Recovery", False),
            SplitDay("Sun", "Recovery", False),
        ]

    if days_per_week == 5:
        if goal == FitGoalType.ATHLETIC_PERFORMANCE.value:
            return [
                SplitDay("Mon", "Power", True),
                SplitDay("Tue", "Conditioning", True),
                SplitDay("Wed", "Strength", True),
                SplitDay("Thu", "Recovery", False),
                SplitDay("Fri", "Athletic Full Body", True),
                SplitDay("Sat", "Engine / Zone 2", True),
                SplitDay("Sun", "Recovery", False),
            ]
        return [
            SplitDay("Mon", "Push", True),
            SplitDay("Tue", "Pull", True),
            SplitDay("Wed", "Legs", True),
            SplitDay("Thu", "Recovery", False),
            SplitDay("Fri", "Upper", True),
            SplitDay("Sat", "Lower", True),
            SplitDay("Sun", "Recovery", False),
        ]

    return [
        SplitDay("Mon", "Push", True),
        SplitDay("Tue", "Pull", True),
        SplitDay("Wed", "Legs", True),
        SplitDay("Thu", "Push", True),
        SplitDay("Fri", "Pull", True),
        SplitDay("Sat", "Legs", True),
        SplitDay("Sun", "Recovery", False),
    ]


def _equipment_label(training_access: List[str]) -> str:
    access = set(training_access or [])
    if "full_gym" in access:
        return "full_gym"
    if "dumbbells_only" in access:
        return "dumbbells"
    if "resistance_bands" in access and "bodyweight_only" in access:
        return "bands_bodyweight"
    if "resistance_bands" in access:
        return "bands"
    return "bodyweight"


def _exercise_pool(equipment_mode: str) -> Dict[str, List[Dict[str, Any]]]:
    full = {
        "push": [
            {"name": "Incline DB Press", "group": "upper_chest"},
            {"name": "Machine Chest Press", "group": "chest"},
            {"name": "DB Shoulder Press", "group": "shoulders"},
            {"name": "Cable Lateral Raise", "group": "shoulders"},
            {"name": "Triceps Rope Pressdown", "group": "triceps"},
        ],
        "pull": [
            {"name": "Lat Pulldown", "group": "lats"},
            {"name": "Chest Supported Row", "group": "upper_back"},
            {"name": "Face Pull", "group": "rear_delts"},
            {"name": "DB Curl", "group": "biceps"},
            {"name": "Hammer Curl", "group": "biceps"},
        ],
        "legs": [
            {"name": "Hack Squat", "group": "quads"},
            {"name": "Romanian Deadlift", "group": "hamstrings"},
            {"name": "Leg Press", "group": "quads"},
            {"name": "Walking Lunge", "group": "glutes"},
            {"name": "Standing Calf Raise", "group": "calves"},
        ],
        "full_body": [
            {"name": "Goblet Squat", "group": "quads"},
            {"name": "DB Romanian Deadlift", "group": "hamstrings"},
            {"name": "Push Up", "group": "chest"},
            {"name": "One-Arm Row", "group": "back"},
            {"name": "Farmer Carry", "group": "core"},
        ],
    }
    if equipment_mode == "full_gym":
        return full
    if equipment_mode == "dumbbells":
        return {
            "push": [
                {"name": "DB Incline Press", "group": "upper_chest"},
                {"name": "DB Floor Press", "group": "chest"},
                {"name": "DB Shoulder Press", "group": "shoulders"},
                {"name": "DB Lateral Raise", "group": "shoulders"},
                {"name": "Overhead DB Triceps Extension", "group": "triceps"},
            ],
            "pull": [
                {"name": "One-Arm DB Row", "group": "lats"},
                {"name": "Chest-Supported DB Row", "group": "upper_back"},
                {"name": "Rear Delt Fly", "group": "rear_delts"},
                {"name": "DB Curl", "group": "biceps"},
                {"name": "Cross-Body Hammer Curl", "group": "biceps"},
            ],
            "legs": [
                {"name": "DB Goblet Squat", "group": "quads"},
                {"name": "DB Romanian Deadlift", "group": "hamstrings"},
                {"name": "Split Squat", "group": "glutes"},
                {"name": "Step-Up", "group": "quads"},
                {"name": "Single-Leg Calf Raise", "group": "calves"},
            ],
            "full_body": full["full_body"],
        }
    return {
        "push": [
            {"name": "Push Up", "group": "chest"},
            {"name": "Pike Push Up", "group": "shoulders"},
            {"name": "Band Chest Press", "group": "chest"},
            {"name": "Band Overhead Press", "group": "shoulders"},
            {"name": "Bench Dip", "group": "triceps"},
        ],
        "pull": [
            {"name": "Band Row", "group": "back"},
            {"name": "Bodyweight Inverted Row", "group": "back"},
            {"name": "Band Face Pull", "group": "rear_delts"},
            {"name": "Band Curl", "group": "biceps"},
            {"name": "Doorframe Isometric Row", "group": "lats"},
        ],
        "legs": [
            {"name": "Bodyweight Squat", "group": "quads"},
            {"name": "Split Squat", "group": "glutes"},
            {"name": "Single-Leg RDL", "group": "hamstrings"},
            {"name": "Glute Bridge", "group": "glutes"},
            {"name": "Calf Raise", "group": "calves"},
        ],
        "full_body": [
            {"name": "Bodyweight Squat", "group": "quads"},
            {"name": "Hip Hinge Drill", "group": "hamstrings"},
            {"name": "Push Up", "group": "chest"},
            {"name": "Band Row", "group": "back"},
            {"name": "Farmer Carry (Household Load)", "group": "core"},
        ],
    }


class FitmaxService:
    def _compute_targets(self, profile: FitmaxProfileInput) -> FitmaxTargets:
        sex_factor = 5 if profile.biological_sex.value == "male" else -161
        bmr = (
            (10 * profile.weight_kg)
            + (6.25 * profile.height_cm)
            - (5 * profile.age)
            + sex_factor
        )
        multiplier = ACTIVITY_MULTIPLIER.get(profile.activity_level.value, 1.55)
        tdee = int(round(bmr * multiplier))

        goal_delta = {
            FitGoalType.LOSE_WEIGHT.value: -450,
            FitGoalType.GAIN_MUSCLE.value: 300,
            FitGoalType.RECOMP.value: -100,
            FitGoalType.MAINTAIN.value: 0,
            FitGoalType.ATHLETIC_PERFORMANCE.value: 150,
        }[profile.goal_type.value]
        calorie_target = max(1200, tdee + goal_delta)

        protein_g = int(round(profile.weight_kg * 2.0))
        fats_g = int(round((0.28 * calorie_target) / 9))
        remaining = max(0, calorie_target - (protein_g * 4) - (fats_g * 9))
        carbs_g = int(round(remaining / 4))

        summary = {
            FitGoalType.LOSE_WEIGHT.value: "Deficit with high protein to preserve muscle while cutting.",
            FitGoalType.GAIN_MUSCLE.value: "Controlled surplus with hard training to maximize lean gain.",
            FitGoalType.RECOMP.value: "Near-maintenance intake with progressive training for slow recomposition.",
            FitGoalType.MAINTAIN.value: "Maintenance calories with resistance training for shape and tone.",
            FitGoalType.ATHLETIC_PERFORMANCE.value: "Performance-first fueling with enough carbs for output.",
        }[profile.goal_type.value]

        return FitmaxTargets(
            tdee=tdee,
            calorie_target=calorie_target,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fats_g=fats_g,
            summary=summary,
        )

    def _build_week_plan(self, profile: FitmaxProfileInput, week_number: int = 1) -> WorkoutWeekPlan:
        split = _build_split(profile.weekly_training_days, profile.goal_type.value)
        training_access = [x.value if hasattr(x, "value") else str(x) for x in profile.training_access]
        equipment_mode = _equipment_label(training_access)
        pool = _exercise_pool(equipment_mode)

        overload_sets_bonus = 1 if week_number in {4, 8, 12, 16} else 0
        base_sets = 3 + overload_sets_bonus

        sessions: List[WorkoutSessionPlan] = []
        for day in split:
            if not day.training:
                sessions.append(
                    WorkoutSessionPlan(
                        day_label=day.day_label,
                        focus=day.focus,
                        estimated_duration_minutes=20,
                        is_training_day=False,
                        motivational_cue="Recovery day. Hit protein and sleep so tomorrow moves feel sharp.",
                        exercises=[],
                    )
                )
                continue

            focus_key = "full_body"
            f = day.focus.lower()
            if "push" in f or "upper" in f:
                focus_key = "push"
            elif "pull" in f:
                focus_key = "pull"
            elif "leg" in f or "lower" in f:
                focus_key = "legs"

            cards: List[WorkoutExercise] = []
            for idx, ex in enumerate(pool[focus_key][:5]):
                reps = "6-10" if idx < 2 else "10-15"
                cards.append(
                    WorkoutExercise(
                        exercise_id=f"{focus_key}-{idx+1}",
                        name=ex["name"],
                        muscle_group=ex["group"],
                        equipment=equipment_mode,
                        sets=base_sets if idx < 3 else max(2, base_sets - 1),
                        reps=reps,
                        rest_seconds=120 if idx < 2 else 75,
                        cues=[
                            "Control the eccentric and own the bottom position.",
                            "Stop 1-2 reps before form breaks.",
                            "Track reps and load to beat next week.",
                        ],
                        swaps=[f"{ex['name']} (variation A)", f"{ex['name']} (variation B)"],
                    )
                )

            cue = {
                FitGoalType.LOSE_WEIGHT.value: "Deficit makes this hard. Good training keeps muscle on your frame.",
                FitGoalType.GAIN_MUSCLE.value: "Surplus gives material. This session turns it into tissue.",
                FitGoalType.RECOMP.value: "Recomp is slow. This quality session is how recomposition happens.",
                FitGoalType.MAINTAIN.value: "Maintenance can still transform your look if intensity stays honest.",
                FitGoalType.ATHLETIC_PERFORMANCE.value: "Today builds usable output, not just gym numbers.",
            }[profile.goal_type.value]

            sessions.append(
                WorkoutSessionPlan(
                    day_label=day.day_label,
                    focus=day.focus,
                    estimated_duration_minutes=profile.preferred_session_length,
                    is_training_day=True,
                    motivational_cue=cue,
                    exercises=cards,
                )
            )

        return WorkoutWeekPlan(
            week_number=week_number,
            goal_type=profile.goal_type,
            sessions=sessions,
        )

    async def get_profile_row(self, user_id: str, db: AsyncSession) -> Optional[FitmaxProfile]:
        result = await db.execute(
            select(FitmaxProfile).where(FitmaxProfile.user_id == UUID(user_id))
        )
        return result.scalar_one_or_none()

    async def get_or_create_week_state(self, user_id: str, db: AsyncSession, dt: Optional[datetime] = None) -> FitmaxWeekState:
        now = dt or datetime.utcnow()
        iso_year, iso_week, _ = now.isocalendar()
        iso_key = f"{iso_year}-W{iso_week:02d}"
        result = await db.execute(
            select(FitmaxWeekState).where(
                (FitmaxWeekState.user_id == UUID(user_id))
                & (FitmaxWeekState.iso_week == iso_key)
            )
        )
        row = result.scalar_one_or_none()
        if row:
            return row

        profile = await self.get_profile_row(user_id, db)
        workout_target = profile.weekly_training_days if profile else 3
        row = FitmaxWeekState(
            user_id=UUID(user_id),
            iso_week=iso_key,
            state={
                "workouts_completed": 0,
                "workout_target": workout_target,
                "calories_logged_days": 0,
                "protein_target_hits": 0,
                "missed_workout_streak": 0,
                "under_target_days": 0,
                "over_target_days": 0,
                "flags": [],
            },
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return row

    async def upsert_profile(self, user_id: str, data: FitmaxProfileInput, db: AsyncSession) -> FitmaxProfileResponse:
        row = await self.get_profile_row(user_id, db)
        targets = self._compute_targets(data)
        week_plan = self._build_week_plan(data, week_number=1)

        payload = data.model_dump()
        if payload.get("training_access"):
            payload["training_access"] = [x.value if hasattr(x, "value") else str(x) for x in payload["training_access"]]

        plan_meta = {
            "split_preview": [f"{s.day_label}: {s.focus}" for s in week_plan.sessions],
            "updated_from": "fitmax_onboarding",
            "generated_at": datetime.utcnow().isoformat(),
        }
        onboarding_state = {"completed": True, "last_updated": datetime.utcnow().isoformat()}

        if not row:
            row = FitmaxProfile(
                user_id=UUID(user_id),
                goal_type=data.goal_type.value,
                biological_sex=data.biological_sex.value,
                age=data.age,
                height_cm=data.height_cm,
                weight_kg=data.weight_kg,
                body_fat_percent=data.body_fat_percent,
                training_access=payload["training_access"],
                weekly_training_days=data.weekly_training_days,
                preferred_session_length=data.preferred_session_length,
                preferred_time_of_day=data.preferred_time_of_day.value,
                activity_level=data.activity_level.value,
                dietary_restrictions=data.dietary_restrictions,
                calorie_tracking=data.calorie_tracking.value,
                eating_goal=data.eating_goal.value,
                wake_time=_parse_hhmm(data.wake_time, "07:00") if data.wake_time else None,
                sleep_time=_parse_hhmm(data.sleep_time, "23:00") if data.sleep_time else None,
                timezone=data.timezone or "UTC",
                quiet_hours_start=_parse_hhmm(data.quiet_hours_start, "22:30") if data.quiet_hours_start else None,
                quiet_hours_end=_parse_hhmm(data.quiet_hours_end, "06:30") if data.quiet_hours_end else None,
                targets=targets.model_dump(),
                plan_meta=plan_meta,
                onboarding_state=onboarding_state,
            )
            db.add(row)
        else:
            row.goal_type = data.goal_type.value
            row.biological_sex = data.biological_sex.value
            row.age = data.age
            row.height_cm = data.height_cm
            row.weight_kg = data.weight_kg
            row.body_fat_percent = data.body_fat_percent
            row.training_access = payload["training_access"]
            row.weekly_training_days = data.weekly_training_days
            row.preferred_session_length = data.preferred_session_length
            row.preferred_time_of_day = data.preferred_time_of_day.value
            row.activity_level = data.activity_level.value
            row.dietary_restrictions = data.dietary_restrictions
            row.calorie_tracking = data.calorie_tracking.value
            row.eating_goal = data.eating_goal.value
            row.wake_time = _parse_hhmm(data.wake_time, row.wake_time or "07:00") if data.wake_time else row.wake_time
            row.sleep_time = _parse_hhmm(data.sleep_time, row.sleep_time or "23:00") if data.sleep_time else row.sleep_time
            row.timezone = data.timezone or row.timezone
            row.quiet_hours_start = _parse_hhmm(data.quiet_hours_start, row.quiet_hours_start or "22:30") if data.quiet_hours_start else row.quiet_hours_start
            row.quiet_hours_end = _parse_hhmm(data.quiet_hours_end, row.quiet_hours_end or "06:30") if data.quiet_hours_end else row.quiet_hours_end
            row.targets = targets.model_dump()
            row.plan_meta = plan_meta
            row.onboarding_state = onboarding_state
            row.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(row)

        await self.refresh_fitmax_schedule(user_id, db)

        profile_obj = FitmaxProfileInput(**{
            "goal_type": row.goal_type,
            "height_cm": row.height_cm,
            "weight_kg": row.weight_kg,
            "age": row.age,
            "biological_sex": row.biological_sex,
            "body_fat_percent": row.body_fat_percent,
            "training_access": row.training_access or [],
            "weekly_training_days": row.weekly_training_days,
            "preferred_session_length": row.preferred_session_length,
            "preferred_time_of_day": row.preferred_time_of_day,
            "activity_level": row.activity_level,
            "dietary_restrictions": row.dietary_restrictions or [],
            "calorie_tracking": row.calorie_tracking,
            "eating_goal": row.eating_goal,
            "wake_time": row.wake_time,
            "sleep_time": row.sleep_time,
            "timezone": row.timezone or "UTC",
            "quiet_hours_start": row.quiet_hours_start,
            "quiet_hours_end": row.quiet_hours_end,
        })

        return FitmaxProfileResponse(
            user_id=user_id,
            profile=profile_obj,
            targets=FitmaxTargets(**(row.targets or {})),
            updated_at=row.updated_at or datetime.utcnow(),
        )

    async def get_profile_response(self, user_id: str, db: AsyncSession) -> Optional[FitmaxProfileResponse]:
        row = await self.get_profile_row(user_id, db)
        if not row:
            return None
        profile_obj = FitmaxProfileInput(**{
            "goal_type": row.goal_type,
            "height_cm": row.height_cm,
            "weight_kg": row.weight_kg,
            "age": row.age,
            "biological_sex": row.biological_sex,
            "body_fat_percent": row.body_fat_percent,
            "training_access": row.training_access or [],
            "weekly_training_days": row.weekly_training_days,
            "preferred_session_length": row.preferred_session_length,
            "preferred_time_of_day": row.preferred_time_of_day,
            "activity_level": row.activity_level,
            "dietary_restrictions": row.dietary_restrictions or [],
            "calorie_tracking": row.calorie_tracking,
            "eating_goal": row.eating_goal,
            "wake_time": row.wake_time,
            "sleep_time": row.sleep_time,
            "timezone": row.timezone or "UTC",
            "quiet_hours_start": row.quiet_hours_start,
            "quiet_hours_end": row.quiet_hours_end,
        })
        targets = FitmaxTargets(**(row.targets or {}))
        return FitmaxProfileResponse(
            user_id=user_id,
            profile=profile_obj,
            targets=targets,
            updated_at=row.updated_at or datetime.utcnow(),
        )

    async def get_week_plan(self, user_id: str, db: AsyncSession, week_number: int = 1) -> WorkoutWeekPlan:
        profile_resp = await self.get_profile_response(user_id, db)
        if not profile_resp:
            raise ValueError("Fitmax profile not found")
        return self._build_week_plan(profile_resp.profile, week_number=week_number)

    async def get_personalized_modules(self, user_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
        profile_resp = await self.get_profile_response(user_id, db)
        if not profile_resp:
            return []
        week_plan = self._build_week_plan(profile_resp.profile, 1)
        split_summary = ", ".join(
            f"{s.day_label}: {s.focus}" for s in week_plan.sessions
        )
        week_preview = " | ".join(
            f"{s.day_label} {s.focus}" for s in week_plan.sessions
        )
        return build_fitmax_course_modules(
            profile_resp.profile.goal_type.value,
            split_summary,
            week_preview,
        )

    async def refresh_fitmax_schedule(self, user_id: str, db: AsyncSession) -> None:
        profile_resp = await self.get_profile_response(user_id, db)
        if not profile_resp:
            return
        profile = profile_resp.profile
        week_plan = self._build_week_plan(profile, 1)

        existing_result = await db.execute(
            select(UserSchedule).where(
                (UserSchedule.user_id == UUID(user_id))
                & (UserSchedule.maxx_id == "fitmax")
                & (UserSchedule.is_active == True)
            ).order_by(UserSchedule.created_at.desc())
        )
        rows = existing_result.scalars().all()
        active = rows[0] if rows else None
        for stale in rows[1:]:
            stale.is_active = False
            stale.updated_at = datetime.utcnow()

        tz_name = profile.timezone or "UTC"
        try:
            user_tz = ZoneInfo(tz_name)
        except Exception:
            user_tz = ZoneInfo("UTC")
        today = datetime.now(user_tz).date()
        morning_time = {
            "morning": "07:30",
            "afternoon": "09:30",
            "evening": "10:00",
        }.get(profile.preferred_time_of_day.value, "08:00")
        midday_time = "14:00"
        evening_time = "20:30"

        days: List[Dict[str, Any]] = []
        for idx, session in enumerate(week_plan.sessions):
            day_date = today + timedelta(days=idx)
            day_tasks: List[Dict[str, Any]] = []
            if session.is_training_day:
                day_tasks.append({
                    "task_id": f"fitmax-{idx}-morning",
                    "time": morning_time,
                    "title": f"{session.focus} today",
                    "description": "fitmax:morning_training",
                    "task_type": "reminder",
                    "duration_minutes": 1,
                    "status": "pending",
                    "notification_sent": False,
                    "chat_reminded": False,
                    "fitmax_message_type": "morning_training",
                    "fitmax_focus": session.focus,
                    "fitmax_day": session.day_label,
                })
                day_tasks.append({
                    "task_id": f"fitmax-{idx}-midday",
                    "time": midday_time,
                    "title": "Workout check-in",
                    "description": "fitmax:midday_training_check",
                    "task_type": "reminder",
                    "duration_minutes": 1,
                    "status": "pending",
                    "notification_sent": False,
                    "chat_reminded": False,
                    "fitmax_message_type": "midday_training_check",
                    "fitmax_focus": session.focus,
                    "fitmax_day": session.day_label,
                })
            else:
                day_tasks.append({
                    "task_id": f"fitmax-{idx}-morning-rest",
                    "time": morning_time,
                    "title": "Rest day recovery",
                    "description": "fitmax:morning_rest",
                    "task_type": "reminder",
                    "duration_minutes": 1,
                    "status": "pending",
                    "notification_sent": False,
                    "chat_reminded": False,
                    "fitmax_message_type": "morning_rest",
                    "fitmax_day": session.day_label,
                })

            day_tasks.append({
                "task_id": f"fitmax-{idx}-evening",
                "time": evening_time,
                "title": "Nutrition consistency check",
                "description": "fitmax:evening_nutrition",
                "task_type": "reminder",
                "duration_minutes": 1,
                "status": "pending",
                "notification_sent": False,
                "chat_reminded": False,
                "fitmax_message_type": "evening_nutrition",
                "fitmax_day": session.day_label,
            })

            if day_date.weekday() == 6:
                day_tasks.append({
                    "task_id": f"fitmax-{idx}-weekly",
                    "time": "19:00",
                    "title": "Weekly summary",
                    "description": "fitmax:weekly_summary",
                    "task_type": "checkpoint",
                    "duration_minutes": 2,
                    "status": "pending",
                    "notification_sent": False,
                    "chat_reminded": False,
                    "fitmax_message_type": "weekly_summary",
                })

            days.append({
                "day_number": idx + 1,
                "date": day_date.isoformat(),
                "tasks": day_tasks,
                "motivation_message": session.motivational_cue or "",
            })

        prefs = {
            "notifications_enabled": True,
            "notification_minutes_before": 0,
            "timezone": profile.timezone or "UTC",
        }
        schedule_context = {
            "source": "fitmax",
            "goal_type": profile.goal_type.value,
            "weekly_training_days": profile.weekly_training_days,
            "protein_target_g": profile_resp.targets.protein_g,
        }

        if not active:
            active = UserSchedule(
                user_id=UUID(user_id),
                schedule_type="maxx",
                maxx_id="fitmax",
                course_title="FitMax Coach",
                days=days,
                preferences=prefs,
                schedule_context=schedule_context,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completion_stats={"completed": 0, "total": 0, "skipped": 0},
            )
            db.add(active)
        else:
            active.course_title = "FitMax Coach"
            active.days = days
            active.preferences = prefs
            active.schedule_context = schedule_context
            active.updated_at = datetime.utcnow()
            active.is_active = True

        await db.commit()

    async def render_coach_message(self, user_id: str, db: AsyncSession, task: Dict[str, Any]) -> str:
        profile_resp = await self.get_profile_response(user_id, db)
        user = await db.get(User, UUID(user_id))
        week_state = await self.get_or_create_week_state(user_id, db)
        state = week_state.state or {}
        name = (user.first_name if user and user.first_name else (user.email.split("@")[0] if user else "bro"))

        if not profile_resp:
            return "Fitmax is ready when you are. Open Fitmax and finish your profile first."

        targets = profile_resp.targets
        msg_type = task.get("fitmax_message_type")
        focus = task.get("fitmax_focus", "training")

        if msg_type == "morning_training":
            return (
                f"Morning {name}. Today is {focus}. "
                f"Goal cue: {profile_resp.targets.summary} Open Fitmax and start session when ready."
            )
        if msg_type == "midday_training_check":
            done = state.get("workouts_completed", 0)
            target = state.get("workout_target", profile_resp.profile.weekly_training_days)
            return (
                f"Quick check: logged {done}/{target} workouts this week. "
                "You still training today? No pressure, just lock it in."
            )
        if msg_type == "morning_rest":
            return (
                "Rest day today. Recovery still counts. "
                f"Hit protein target ({targets.protein_g}g) and prioritize sleep tonight."
            )
        if msg_type == "weekly_summary":
            done = state.get("workouts_completed", 0)
            target = state.get("workout_target", profile_resp.profile.weekly_training_days)
            protein_hits = state.get("protein_target_hits", 0)
            return (
                f"Fitmax week recap: {done}/{target} workouts, protein hit {protein_hits}/7 days. "
                "Keep the same consistency next week and we level up fast."
            )
        remaining = max(0, targets.calorie_target - int(state.get("today_calories", 0)))
        return (
            f"Evening check: about {remaining} kcal left vs target. "
            f"Try to finish near {targets.protein_g}g protein for the day."
        )

    async def log_workout(self, user_id: str, payload: WorkoutSessionLogRequest, db: AsyncSession) -> Dict[str, Any]:
        duration = int(max(1, (payload.completed_at - payload.started_at).total_seconds() // 60))
        row = FitmaxWorkoutLog(
            user_id=UUID(user_id),
            week_number=payload.week_number,
            day_label=payload.day_label,
            focus=payload.focus,
            started_at=payload.started_at,
            completed_at=payload.completed_at,
            duration_minutes=duration,
            feeling_score=payload.feeling_score,
            total_volume_kg=float(payload.total_volume_kg or 0),
            notes=payload.notes,
            sets=[s.model_dump() for s in payload.sets],
            created_at=datetime.utcnow(),
        )
        db.add(row)

        week_state = await self.get_or_create_week_state(user_id, db, payload.completed_at)
        state = week_state.state or {}
        state["workouts_completed"] = int(state.get("workouts_completed", 0)) + 1
        state["missed_workout_streak"] = 0
        state["last_workout_day"] = payload.completed_at.isoformat()
        week_state.state = state
        week_state.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(row)
        return {
            "session_id": str(row.id),
            "duration_minutes": duration,
            "total_volume_kg": row.total_volume_kg,
        }

    async def log_nutrition(self, user_id: str, payload: NutritionLogRequest, db: AsyncSession) -> Dict[str, Any]:
        logged_at = payload.logged_at or datetime.utcnow()
        row = FitmaxNutritionLog(
            user_id=UUID(user_id),
            meal_name=payload.meal_name,
            meal_type=payload.meal_type,
            calories=payload.calories,
            protein_g=payload.protein_g,
            carbs_g=payload.carbs_g,
            fats_g=payload.fats_g,
            food_items=payload.food_items,
            logged_at=logged_at,
            created_at=datetime.utcnow(),
        )
        db.add(row)

        profile = await self.get_profile_response(user_id, db)
        week_state = await self.get_or_create_week_state(user_id, db, logged_at)
        state = week_state.state or {}
        state["today_calories"] = int(state.get("today_calories", 0)) + payload.calories
        state["today_protein"] = int(state.get("today_protein", 0)) + payload.protein_g
        if profile and state["today_protein"] >= profile.targets.protein_g:
            state["protein_target_hits"] = int(state.get("protein_target_hits", 0)) + 1
            state["today_protein"] = 0
        week_state.state = state
        week_state.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(row)
        return {"log_id": str(row.id)}

    async def get_daily_nutrition(self, user_id: str, db: AsyncSession, day: Optional[date] = None) -> Dict[str, Any]:
        day_val = day or datetime.utcnow().date()
        start = datetime.combine(day_val, datetime.min.time())
        end = datetime.combine(day_val, datetime.max.time())
        result = await db.execute(
            select(
                func.coalesce(func.sum(FitmaxNutritionLog.calories), 0),
                func.coalesce(func.sum(FitmaxNutritionLog.protein_g), 0),
                func.coalesce(func.sum(FitmaxNutritionLog.carbs_g), 0),
                func.coalesce(func.sum(FitmaxNutritionLog.fats_g), 0),
            ).where(
                (FitmaxNutritionLog.user_id == UUID(user_id))
                & (FitmaxNutritionLog.logged_at >= start)
                & (FitmaxNutritionLog.logged_at <= end)
            )
        )
        calories, protein, carbs, fats = result.one()
        profile = await self.get_profile_response(user_id, db)
        return {
            "date": day_val.isoformat(),
            "consumed": {
                "calories": int(calories),
                "protein_g": int(protein),
                "carbs_g": int(carbs),
                "fats_g": int(fats),
            },
            "target": profile.targets.model_dump() if profile else {},
        }

    async def log_measurements(self, user_id: str, payload: MeasurementLogRequest, db: AsyncSession) -> Dict[str, Any]:
        measured_on = payload.measured_on or datetime.utcnow().date()
        row = FitmaxMeasurementLog(
            user_id=UUID(user_id),
            measured_on=datetime.combine(measured_on, datetime.min.time()),
            weight_kg=payload.weight_kg,
            neck_cm=payload.neck_cm,
            chest_cm=payload.chest_cm,
            waist_cm=payload.waist_cm,
            hips_cm=payload.hips_cm,
            arms_cm=payload.arms_cm,
            thighs_cm=payload.thighs_cm,
            created_at=datetime.utcnow(),
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return {"measurement_id": str(row.id)}

    async def get_progress_overview(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        m_result = await db.execute(
            select(FitmaxMeasurementLog)
            .where(FitmaxMeasurementLog.user_id == UUID(user_id))
            .order_by(FitmaxMeasurementLog.measured_on.asc())
            .limit(52)
        )
        measurements = m_result.scalars().all()

        w_result = await db.execute(
            select(FitmaxWorkoutLog)
            .where(FitmaxWorkoutLog.user_id == UUID(user_id))
            .order_by(FitmaxWorkoutLog.created_at.desc())
            .limit(100)
        )
        workouts = w_result.scalars().all()

        total_volume = sum(float(w.total_volume_kg or 0) for w in workouts)
        return {
            "measurements": [
                {
                    "id": str(m.id),
                    "measured_on": m.measured_on.isoformat() if m.measured_on else None,
                    "weight_kg": m.weight_kg,
                    "waist_cm": m.waist_cm,
                    "chest_cm": m.chest_cm,
                    "hips_cm": m.hips_cm,
                    "arms_cm": m.arms_cm,
                    "thighs_cm": m.thighs_cm,
                }
                for m in measurements
            ],
            "performance": {
                "sessions_logged": len(workouts),
                "total_volume_kg": round(total_volume, 2),
                "latest_sessions": [
                    {
                        "id": str(w.id),
                        "focus": w.focus,
                        "day_label": w.day_label,
                        "duration_minutes": w.duration_minutes,
                        "total_volume_kg": float(w.total_volume_kg or 0),
                        "completed_at": w.completed_at.isoformat() if w.completed_at else None,
                    }
                    for w in workouts[:20]
                ],
            },
        }

    async def build_dashboard(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        profile = await self.get_profile_response(user_id, db)
        if not profile:
            raise ValueError("Fitmax profile not found")
        week_state = await self.get_or_create_week_state(user_id, db)
        week_plan = await self.get_week_plan(user_id, db, week_number=1)
        state = week_state.state or {}
        return {
            "profile": profile.model_dump(),
            "current_week": 1,
            "week_state": state,
            "weekly_summary": {
                "workouts_completed": int(state.get("workouts_completed", 0)),
                "workouts_target": int(state.get("workout_target", profile.profile.weekly_training_days)),
                "protein_target_hits": int(state.get("protein_target_hits", 0)),
            },
            "plan_preview": week_plan.model_dump(),
        }

    async def seed_welcome_message_if_needed(self, user_id: str, db: AsyncSession) -> None:
        result = await db.execute(
            select(ChatHistory)
            .where(
                (ChatHistory.user_id == UUID(user_id))
                & (ChatHistory.role == "coach")
            )
            .order_by(ChatHistory.created_at.asc())
            .limit(1)
        )
        first = result.scalar_one_or_none()
        if first:
            return
        db.add(
            ChatHistory(
                user_id=UUID(user_id),
                role="coach",
                content="Fitmax coach here. Set up your Fitmax profile so I can personalize workouts and daily check-ins.",
                created_at=datetime.utcnow(),
            )
        )
        await db.commit()


fitmax_service = FitmaxService()
