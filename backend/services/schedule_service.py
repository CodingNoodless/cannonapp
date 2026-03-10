"""
Schedule Service - AI-powered personalised schedule generation using Gemini
Generates, adapts, and manages user schedules for course modules.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from bson import ObjectId
from config import settings
from db import get_database
from services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

# ── Gemini prompt for schedule generation ──────────────────────────────────────

SCHEDULE_GENERATION_PROMPT = """You are an expert fitness and self-improvement coach specialising in lookmaxxing.
Your job is to create a PERSONALISED daily schedule for a user working on a specific module.

## MODULE INFO
Title: {module_title}
Description: {module_description}

## MODULE GUIDELINES (loose — use your expertise to flesh these out)
Exercises: {exercises}
Frequency hints: {frequency_hints}
Duration ranges: {duration_ranges}
Tips: {tips}
Difficulty progression: {difficulty_progression}
Focus areas: {focus_areas}

## USER CONTEXT
Wake time: {wake_time}
Sleep time: {sleep_time}
Preferred workout times: {preferred_times}
Days to generate: {num_days}
{user_history_context}

## INSTRUCTIONS
1. Create a schedule for {num_days} days.
2. Space tasks throughout the day between wake and sleep times.
3. Make each day slightly different to prevent boredom.
4. Gradually increase intensity / duration over the days.
5. Include motivational messages for each day.
6. Each task must have: task_id (uuid), time (HH:MM), title, description, task_type (exercise/routine/reminder/checkpoint), duration_minutes.
7. Adapt based on user history if provided — if they skip certain tasks, reduce those; if they complete everything, ramp up.

## OUTPUT FORMAT
Return ONLY valid JSON matching this structure (no markdown fences):
{{
  "days": [
    {{
      "day_number": 1,
      "tasks": [
        {{
          "task_id": "uuid-string",
          "time": "07:00",
          "title": "Morning Mewing Session",
          "description": "Place tongue flat against roof of mouth...",
          "task_type": "exercise",
          "duration_minutes": 15
        }}
      ],
      "motivation_message": "Day 1! Let's build that jawline. Consistency is king."
    }}
  ]
}}
"""

SCHEDULE_ADAPTATION_PROMPT = """You are an expert fitness coach. A user wants to ADAPT their existing schedule.

## CURRENT SCHEDULE
{current_schedule_json}

## COMPLETION STATS
Tasks completed: {completed_count}/{total_count}
Most skipped task types: {most_skipped}
Average completion rate: {completion_rate}%

## USER FEEDBACK
"{user_feedback}"

## INSTRUCTIONS
Modify the remaining days of the schedule based on the feedback and completion data.
- If the user says "too hard", reduce intensity/duration.
- If "too easy", increase it.
- If they skip morning tasks, move them later.
- Keep the same JSON structure as the input.

Return ONLY valid JSON with the updated "days" array.
"""


class ScheduleService:
    """AI-powered schedule generation and management"""

    def __init__(self):
        self.gemini = GeminiService()

    async def generate_schedule(
        self,
        user_id: str,
        course_id: str,
        module_number: int,
        preferences: Optional[dict] = None,
        num_days: int = 7,
    ) -> dict:
        """
        Generate a personalised schedule for a user's course module.
        Uses Gemini to create the schedule based on module guidelines and user context.
        """
        db = get_database()

        # Fetch course and module
        from bson import ObjectId
        course = await db.courses.find_one({"_id": ObjectId(course_id)})
        if not course:
            raise ValueError("Course not found")

        module = None
        for m in course.get("modules", []):
            if m.get("module_number") == module_number:
                module = m
                break
        if not module:
            raise ValueError(f"Module {module_number} not found in course")

        # Get user context for adaptation
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        user_history_context = await self._build_user_context(db, user_id, course_id)

        # Parse preferences
        prefs = preferences or {}
        wake_time = prefs.get("wake_time", "07:00")
        sleep_time = prefs.get("sleep_time", "23:00")
        preferred_times = prefs.get("preferred_workout_times", ["08:00", "18:00"])

        # Extract guidelines
        guidelines = module.get("guidelines", {}) or {}

        # Use module's recommended_days if num_days wasn't explicitly overridden
        if num_days == 7 and guidelines.get("recommended_days"):
            num_days = guidelines["recommended_days"]

        # Build prompt
        prompt = SCHEDULE_GENERATION_PROMPT.format(
            module_title=module.get("title", ""),
            module_description=module.get("description", ""),
            exercises=", ".join(guidelines.get("exercises", ["General exercises"])),
            frequency_hints=", ".join(guidelines.get("frequency_hints", ["Daily"])),
            duration_ranges=", ".join(guidelines.get("duration_ranges", ["15-30 min"])),
            tips=", ".join(guidelines.get("tips", ["Stay consistent"])),
            difficulty_progression=guidelines.get("difficulty_progression", "gradual"),
            focus_areas=", ".join(guidelines.get("focus_areas", ["Overall improvement"])),
            wake_time=wake_time,
            sleep_time=sleep_time,
            preferred_times=", ".join(preferred_times),
            num_days=num_days,
            user_history_context=user_history_context,
        )

        # Call Gemini
        try:
            import google.generativeai as genai

            model = genai.GenerativeModel(settings.gemini_model)
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                ),
            )
            schedule_data = json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini schedule generation failed: {e}")
            schedule_data = self._generate_fallback_schedule(module, num_days, wake_time)

        # Ensure every task has a task_id
        for day in schedule_data.get("days", []):
            for task in day.get("tasks", []):
                if not task.get("task_id"):
                    task["task_id"] = str(uuid.uuid4())
                task.setdefault("status", "pending")
                task.setdefault("notification_sent", False)

        # Assign dates starting from tomorrow
        start_date = datetime.utcnow().date() + timedelta(days=1)
        for day in schedule_data.get("days", []):
            day_num = day.get("day_number", 1)
            day["date"] = (start_date + timedelta(days=day_num - 1)).isoformat()

        # Deactivate any existing active schedule for this SAME module (not all modules)
        await db.user_schedules.update_many(
            {"user_id": user_id, "course_id": course_id, "module_number": module_number, "is_active": True},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}},
        )

        # Store in DB
        schedule_doc = {
            "user_id": user_id,
            "course_id": course_id,
            "course_title": course.get("title", ""),
            "module_number": module_number,
            "days": schedule_data.get("days", []),
            "preferences": prefs,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "adapted_count": 0,
            "user_feedback": [],
            "completion_stats": {"completed": 0, "total": 0, "skipped": 0},
        }
        result = await db.user_schedules.insert_one(schedule_doc)

        schedule_doc["id"] = str(schedule_doc.pop("_id", result.inserted_id))
        return schedule_doc

    async def get_current_schedule(self, user_id: str, course_id: str = None, module_number: int = None) -> Optional[dict]:
        """Get the user's current active schedule(s). Optionally filter by course/module."""
        db = get_database()
        query: dict = {"user_id": user_id, "is_active": True}
        if course_id:
            query["course_id"] = course_id
        if module_number:
            query["module_number"] = module_number

        schedule = await db.user_schedules.find_one(
            query,
            sort=[("created_at", -1)],
        )
        if schedule:
            schedule["id"] = str(schedule.pop("_id"))
        return schedule

    async def get_schedule_by_id(self, schedule_id: str, user_id: str) -> Optional[dict]:
        """Get a specific schedule"""
        from bson import ObjectId
        db = get_database()
        schedule = await db.user_schedules.find_one(
            {"_id": ObjectId(schedule_id), "user_id": user_id}
        )
        if schedule:
            schedule["id"] = str(schedule.pop("_id"))
        return schedule

    async def complete_task(
        self, user_id: str, schedule_id: str, task_id: str, feedback: Optional[str] = None
    ) -> dict:
        """Mark a task as completed and record feedback for adaptation"""
        from bson import ObjectId
        db = get_database()

        schedule = await db.user_schedules.find_one(
            {"_id": ObjectId(schedule_id), "user_id": user_id}
        )
        if not schedule:
            raise ValueError("Schedule not found")

        # Find and update the task
        updated = False
        for day in schedule.get("days", []):
            for task in day.get("tasks", []):
                if task.get("task_id") == task_id:
                    task["status"] = "completed"
                    task["completed_at"] = datetime.utcnow().isoformat()
                    updated = True
                    break
            if updated:
                break

        if not updated:
            raise ValueError("Task not found in schedule")

        # Update completion stats
        stats = schedule.get("completion_stats", {"completed": 0, "total": 0, "skipped": 0})
        stats["completed"] = stats.get("completed", 0) + 1

        # Count total tasks
        total = sum(len(d.get("tasks", [])) for d in schedule.get("days", []))
        stats["total"] = total

        update_data = {
            "days": schedule["days"],
            "completion_stats": stats,
            "updated_at": datetime.utcnow(),
        }

        # Record feedback if provided
        if feedback:
            feedback_entry = {
                "task_id": task_id,
                "feedback": feedback,
                "timestamp": datetime.utcnow().isoformat(),
            }
            update_data["$push"] = {"user_feedback": feedback_entry}
            await db.user_schedules.update_one(
                {"_id": ObjectId(schedule_id)},
                {"$set": {k: v for k, v in update_data.items() if k != "$push"}, "$push": update_data["$push"]},
            )
        else:
            await db.user_schedules.update_one(
                {"_id": ObjectId(schedule_id)},
                {"$set": update_data},
            )

        return {"status": "completed", "completion_stats": stats}

    async def adapt_schedule(self, user_id: str, schedule_id: str, feedback: str) -> dict:
        """Use AI to adapt the schedule based on user feedback and completion data"""
        from bson import ObjectId
        db = get_database()

        schedule = await db.user_schedules.find_one(
            {"_id": ObjectId(schedule_id), "user_id": user_id}
        )
        if not schedule:
            raise ValueError("Schedule not found")

        stats = schedule.get("completion_stats", {})
        total = stats.get("total", 1)
        completed = stats.get("completed", 0)
        completion_rate = round((completed / max(total, 1)) * 100)

        # Find most skipped task types
        skipped_types = []
        for day in schedule.get("days", []):
            for task in day.get("tasks", []):
                if task.get("status") == "skipped":
                    skipped_types.append(task.get("task_type", "unknown"))

        prompt = SCHEDULE_ADAPTATION_PROMPT.format(
            current_schedule_json=json.dumps({"days": schedule["days"]}, indent=2),
            completed_count=completed,
            total_count=total,
            most_skipped=", ".join(set(skipped_types)) if skipped_types else "none",
            completion_rate=completion_rate,
            user_feedback=feedback,
        )

        try:
            import google.generativeai as genai

            model = genai.GenerativeModel(settings.gemini_model)
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(response_mime_type="application/json"),
            )
            adapted = json.loads(response.text)
        except Exception as e:
            logger.error(f"Schedule adaptation failed: {e}")
            raise ValueError(f"Failed to adapt schedule: {e}")

        await db.user_schedules.update_one(
            {"_id": ObjectId(schedule_id)},
            {
                "$set": {
                    "days": adapted.get("days", schedule["days"]),
                    "updated_at": datetime.utcnow(),
                },
                "$inc": {"adapted_count": 1},
                "$push": {
                    "user_feedback": {
                        "type": "adaptation",
                        "feedback": feedback,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                },
            },
        )

        schedule["days"] = adapted.get("days", schedule["days"])
        schedule["id"] = str(schedule.pop("_id", schedule_id))
        schedule["adapted_count"] = schedule.get("adapted_count", 0) + 1
        return schedule

    async def edit_task(
        self, user_id: str, schedule_id: str, task_id: str, updates: dict
    ) -> dict:
        """Edit a task's time, title, description, or duration"""
        from bson import ObjectId
        db = get_database()

        schedule = await db.user_schedules.find_one(
            {"_id": ObjectId(schedule_id), "user_id": user_id}
        )
        if not schedule:
            raise ValueError("Schedule not found")

        updated = False
        updated_task = None
        for day in schedule.get("days", []):
            for task in day.get("tasks", []):
                if task.get("task_id") == task_id:
                    if updates.get("time"):
                        task["time"] = updates["time"]
                    if updates.get("title"):
                        task["title"] = updates["title"]
                    if updates.get("description"):
                        task["description"] = updates["description"]
                    if updates.get("duration_minutes"):
                        task["duration_minutes"] = updates["duration_minutes"]
                    # Reset notification if time changed
                    if updates.get("time"):
                        task["notification_sent"] = False
                    updated = True
                    updated_task = task
                    break
            if updated:
                break

        if not updated:
            raise ValueError("Task not found in schedule")

        await db.user_schedules.update_one(
            {"_id": ObjectId(schedule_id)},
            {"$set": {"days": schedule["days"], "updated_at": datetime.utcnow()}},
        )
        return {"status": "updated", "task": updated_task}

    async def delete_task(
        self, user_id: str, schedule_id: str, task_id: str
    ) -> dict:
        """Remove a task from the schedule"""
        from bson import ObjectId
        db = get_database()

        schedule = await db.user_schedules.find_one(
            {"_id": ObjectId(schedule_id), "user_id": user_id}
        )
        if not schedule:
            raise ValueError("Schedule not found")

        deleted = False
        for day in schedule.get("days", []):
            original_count = len(day.get("tasks", []))
            day["tasks"] = [t for t in day.get("tasks", []) if t.get("task_id") != task_id]
            if len(day["tasks"]) < original_count:
                deleted = True
                break

        if not deleted:
            raise ValueError("Task not found in schedule")

        await db.user_schedules.update_one(
            {"_id": ObjectId(schedule_id)},
            {"$set": {"days": schedule["days"], "updated_at": datetime.utcnow()}},
        )
        return {"status": "deleted"}

    async def update_preferences(self, user_id: str, preferences: dict) -> dict:
        """Update schedule preferences for a user (stored on active schedule)"""
        db = get_database()
        result = await db.user_schedules.update_one(
            {"user_id": user_id, "is_active": True},
            {"$set": {"preferences": preferences, "updated_at": datetime.utcnow()}},
        )
        if result.modified_count == 0:
            # Store preferences on user doc as a fallback
            from bson import ObjectId
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"schedule_preferences": preferences}},
            )
        return {"message": "Preferences updated"}

    # ── Private helpers ────────────────────────────────────────────────────────

    async def _build_user_context(self, db, user_id: str, course_id: str) -> str:
        """Build user history context string for Gemini"""
        lines: list[str] = []

        # Past schedule completion data
        past_schedules = db.user_schedules.find(
            {"user_id": user_id, "course_id": course_id, "is_active": False}
        ).sort("created_at", -1).limit(3)

        past_feedback = []
        async for sched in past_schedules:
            stats = sched.get("completion_stats", {})
            total = stats.get("total", 0)
            completed = stats.get("completed", 0)
            if total > 0:
                lines.append(f"Past schedule: {completed}/{total} tasks completed ({round(completed/total*100)}%)")
            for fb in sched.get("user_feedback", []):
                past_feedback.append(fb.get("feedback", ""))

        if past_feedback:
            lines.append(f"Past feedback: {'; '.join(past_feedback[:5])}")

        # Latest scan data
        latest_scan = await db.scans.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)],
        )
        if latest_scan and latest_scan.get("analysis"):
            metrics = latest_scan["analysis"].get("metrics", {})
            jawline = metrics.get("jawline", {})
            if jawline:
                lines.append(f"User jawline score: {jawline.get('definition_score', 'N/A')}/10")
            overall = metrics.get("overall_score")
            if overall:
                lines.append(f"User overall face score: {overall}/10")

        # Onboarding Personalization Data
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        onboarding = user.get("onboarding", {})
        if onboarding:
            profile_parts = []
            if onboarding.get("gender"): profile_parts.append(f"Gender: {onboarding['gender']}")
            if onboarding.get("age"): profile_parts.append(f"Age: {onboarding['age']}")
            if onboarding.get("height"): profile_parts.append(f"Height: {onboarding['height']}cm")
            if onboarding.get("weight"): profile_parts.append(f"Weight: {onboarding['weight']}kg")
            if profile_parts:
                lines.append("## PHYSICAL PROFILE")
                lines.append(", ".join(profile_parts))

            if onboarding.get("activity_level"):
                lines.append(f"Activity Level: {onboarding['activity_level']}")
            
            if onboarding.get("equipment"):
                lines.append(f"Available Equipment: {', '.join(onboarding['equipment'])}")
            
            if onboarding.get("skin_type"):
                lines.append(f"Skin Type: {onboarding['skin_type']}")

        if lines:
            return "\n## USER CONTEXT & HISTORY\n" + "\n".join(lines)
        return "\nNo prior history available — this is the user's first schedule."

    def _generate_fallback_schedule(self, module: dict, num_days: int, wake_time: str) -> dict:
        """Generate a basic fallback schedule when Gemini fails"""
        guidelines = module.get("guidelines", {}) or {}
        exercises = guidelines.get("exercises", ["General exercise"])

        days = []
        for day_num in range(1, num_days + 1):
            tasks = []
            # Morning session
            tasks.append({
                "task_id": str(uuid.uuid4()),
                "time": wake_time,
                "title": f"Morning {exercises[0] if exercises else 'Exercise'}",
                "description": f"Start your day with a {exercises[0].lower() if exercises else 'exercise'} session.",
                "task_type": "exercise",
                "duration_minutes": 15 + (day_num * 2),  # gradual increase
            })
            # Evening session
            tasks.append({
                "task_id": str(uuid.uuid4()),
                "time": "18:00",
                "title": f"Evening {exercises[-1] if exercises else 'Exercise'}",
                "description": f"End your day strong with {exercises[-1].lower() if exercises else 'exercise'}.",
                "task_type": "exercise",
                "duration_minutes": 15 + (day_num * 2),
            })
            days.append({
                "day_number": day_num,
                "tasks": tasks,
                "motivation_message": f"Day {day_num} — keep pushing! 💪",
            })

        return {"days": days}


# Singleton instance
schedule_service = ScheduleService()
