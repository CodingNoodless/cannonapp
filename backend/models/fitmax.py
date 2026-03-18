"""
Fitmax models - request/response schemas and typed profile objects.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class FitGoalType(str, Enum):
    LOSE_WEIGHT = "lose_weight_cut"
    GAIN_MUSCLE = "gain_muscle_bulk"
    RECOMP = "body_recomposition"
    MAINTAIN = "maintain_tone"
    PERFORMANCE = "athletic_performance"


class BiologicalSex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class TrainingAccessType(str, Enum):
    FULL_GYM = "full_gym"
    DUMBBELLS_ONLY = "dumbbells_only"
    BODYWEIGHT_ONLY = "bodyweight_only"
    RESISTANCE_BANDS = "resistance_bands"
    MIXED = "mixed_varies"


class TimeOfDayPreference(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "lightly_active"
    MODERATE = "moderately_active"
    VERY_ACTIVE = "very_active"


class CalorieTrackingStatus(str, Enum):
    YES = "yes"
    NO = "no"
    WANT_TO_START = "want_to_start"


class EatingGoal(str, Enum):
    EAT_MORE = "eat_more"
    EAT_LESS = "eat_less"
    EAT_BETTER = "eat_better"
    UNSURE = "unsure"


class FitmaxProfileInput(BaseModel):
    goal_type: FitGoalType
    height_cm: float = Field(gt=0)
    weight_kg: float = Field(gt=0)
    age: int = Field(ge=13, le=99)
    biological_sex: BiologicalSex
    body_fat_percent: Optional[float] = Field(default=None, ge=2, le=70)
    training_access: List[TrainingAccessType] = Field(default_factory=list, min_length=1)
    weekly_training_days: int = Field(ge=2, le=6)
    preferred_session_length: Literal[30, 45, 60, 90] = 45
    preferred_time_of_day: TimeOfDayPreference = TimeOfDayPreference.EVENING
    activity_level: ActivityLevel = ActivityLevel.MODERATE
    dietary_restrictions: List[str] = Field(default_factory=list)
    calorie_tracking: CalorieTrackingStatus = CalorieTrackingStatus.NO
    eating_goal: EatingGoal = EatingGoal.UNSURE
    wake_time: Optional[str] = Field(default=None, description="HH:MM in 24h")
    sleep_time: Optional[str] = Field(default=None, description="HH:MM in 24h")
    timezone: str = "UTC"
    quiet_hours_start: Optional[str] = Field(default=None, description="HH:MM in 24h")
    quiet_hours_end: Optional[str] = Field(default=None, description="HH:MM in 24h")


class FitmaxTargets(BaseModel):
    tdee: int
    calorie_target: int
    protein_g: int
    carbs_g: int
    fats_g: int
    summary: str


class FitmaxProfileResponse(BaseModel):
    user_id: str
    profile: FitmaxProfileInput
    targets: FitmaxTargets
    updated_at: datetime


class WorkoutExercise(BaseModel):
    exercise_id: str
    name: str
    muscle_group: str
    equipment: str
    sets: int
    reps: str
    rest_seconds: int
    cues: List[str] = Field(default_factory=list)
    swaps: List[str] = Field(default_factory=list)


class WorkoutSessionPlan(BaseModel):
    day_label: str
    focus: str
    estimated_duration_minutes: int
    is_training_day: bool = True
    motivational_cue: Optional[str] = None
    exercises: List[WorkoutExercise] = Field(default_factory=list)


class WorkoutWeekPlan(BaseModel):
    week_number: int
    goal_type: FitGoalType
    sessions: List[WorkoutSessionPlan] = Field(default_factory=list)


class WorkoutSetLog(BaseModel):
    exercise_id: str
    set_index: int
    reps_completed: int = Field(ge=0)
    weight_kg: Optional[float] = Field(default=None, ge=0)
    duration_seconds: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None


class WorkoutSessionLogRequest(BaseModel):
    started_at: datetime
    completed_at: datetime
    day_label: str
    focus: str
    week_number: int
    feeling_score: Optional[int] = Field(default=None, ge=1, le=5)
    sets: List[WorkoutSetLog] = Field(default_factory=list)
    total_volume_kg: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None


class NutritionLogRequest(BaseModel):
    meal_name: str
    meal_type: Literal["breakfast", "lunch", "dinner", "snacks"]
    calories: int = Field(ge=0)
    protein_g: int = Field(ge=0)
    carbs_g: int = Field(ge=0)
    fats_g: int = Field(ge=0)
    logged_at: Optional[datetime] = None
    food_items: List[str] = Field(default_factory=list)


class MeasurementLogRequest(BaseModel):
    measured_on: Optional[date] = None
    weight_kg: Optional[float] = Field(default=None, gt=0)
    neck_cm: Optional[float] = Field(default=None, gt=0)
    chest_cm: Optional[float] = Field(default=None, gt=0)
    waist_cm: Optional[float] = Field(default=None, gt=0)
    hips_cm: Optional[float] = Field(default=None, gt=0)
    arms_cm: Optional[float] = Field(default=None, gt=0)
    thighs_cm: Optional[float] = Field(default=None, gt=0)


class FitmaxDashboardResponse(BaseModel):
    profile: FitmaxProfileResponse
    current_week: int
    week_state: dict
    weekly_summary: dict
    plan_preview: WorkoutWeekPlan

