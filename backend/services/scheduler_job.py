"""
Scheduler Job - Background task that sends WhatsApp reminders for due schedule tasks.
Uses APScheduler to run every 5 minutes and check for tasks whose time has arrived.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from db import get_database
from services.twilio_service import twilio_service

logger = logging.getLogger(__name__)


async def send_due_notifications():
    """
    Check for schedule tasks that are due and send WhatsApp reminders.
    Runs periodically via APScheduler.
    """
    try:
        db = get_database()
        from zoneinfo import ZoneInfo
        from bson import ObjectId

        # Get all active schedules
        cursor = db.user_schedules.find({"is_active": True})

        async for schedule in cursor:
            user_id = schedule.get("user_id")
            
            # Fetch user to get their timezone
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                continue

            # Determine user's local "now"
            tz_name = user.get("onboarding", {}).get("timezone", "UTC")
            try:
                user_tz = ZoneInfo(tz_name)
            except Exception:
                user_tz = ZoneInfo("UTC")
            
            now_utc = datetime.now(ZoneInfo("UTC"))
            local_now = now_utc.astimezone(user_tz)
            
            current_time = local_now.strftime("%H:%M")
            today_iso = local_now.date().isoformat()

            prefs = schedule.get("preferences", {})
            prefs = schedule.get("preferences", {})

            # Skip if notifications disabled
            if not prefs.get("notifications_enabled", True):
                continue

            # Find today's tasks
            for day in schedule.get("days", []):
                if day.get("date") != today_iso:
                    continue

                for task in day.get("tasks", []):
                    if task.get("notification_sent") or task.get("status") != "pending":
                        continue

                    task_time = task.get("time", "")
                    if not task_time:
                        continue

                    # Check if task is due within the next 5 minutes
                    try:
                        # Improved parsing to handle 12-hour format if it accidentally got saved
                        task_time_clean = task_time.strip().upper()
                        if "AM" in task_time_clean or "PM" in task_time_clean:
                            from datetime import datetime as dt
                            parsed_time = dt.strptime(task_time_clean, "%I:%M %p").time()
                            task_hour, task_min = parsed_time.hour, parsed_time.minute
                        else:
                            task_hour, task_min = map(int, task_time_clean.split(":"))
                        
                        task_dt = local_now.replace(hour=task_hour, minute=task_min, second=0, microsecond=0)
                        
                        reminder_offset = prefs.get("notification_minutes_before", 5)
                        notify_at = task_dt - timedelta(minutes=reminder_offset)

                        if notify_at <= local_now <= task_dt + timedelta(minutes=5):
                            # Send notification
                            if user.get("phone_number"):
                                success = await twilio_service.send_schedule_reminder(
                                    phone=user["phone_number"],
                                    task_title=task.get("title", "Task"),
                                    task_description=task.get("description", ""),
                                    task_time=task_time,
                                )
                                if success:
                                    task["notification_sent"] = True
                                    logger.info(f"Sent reminder to {user_id} for task {task.get('task_id')}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid task time '{task_time}': {e}")
                        continue

            # Persist notification_sent flags
            await db.user_schedules.update_one(
                {"_id": schedule["_id"]},
                {"$set": {"days": schedule["days"], "updated_at": datetime.utcnow()}},
            )

    except Exception as e:
        logger.error(f"Scheduler job error: {e}", exc_info=True)


async def send_daily_progress_prompts():
    """
    Once-per-day WhatsApp prompts asking users for a progress picture.

    Runs periodically (e.g. hourly) and checks, per user, whether we've already
    sent a prompt for *today* in their local timezone. If not, and it's after
    21:00 local time, we send one and stamp last_progress_prompt_date.
    """
    try:
        db = get_database()
        from zoneinfo import ZoneInfo

        now_utc = datetime.utcnow()

        cursor = db.users.find({"phone_number": {"$ne": None}})
        async for user in cursor:
            tz_name = user.get("onboarding", {}).get("timezone", "UTC")
            try:
                user_tz = ZoneInfo(tz_name)
            except Exception:
                user_tz = ZoneInfo("UTC")

            local_now = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(user_tz)
            today_iso = local_now.date().isoformat()
            hour = local_now.hour

            # Only after 9pm local time
            if hour < 21:
                continue

            last_prompt = user.get("last_progress_prompt_date")
            if last_prompt == today_iso:
                continue

            phone = user.get("phone_number")
            if not phone:
                continue

            try:
                success = await twilio_service.send_daily_progress_prompt(
                    phone=phone,
                    name=user.get("first_name") or user.get("email"),
                )
                if success:
                    await db.users.update_one(
                        {"_id": user["_id"]},
                        {"$set": {"last_progress_prompt_date": today_iso, "updated_at": datetime.utcnow()}},
                    )
                    logger.info(f"Sent daily progress prompt to user {user.get('_id')}")
            except Exception as e:
                logger.warning(f"Failed to send daily progress prompt to {user.get('_id')}: {e}")

    except Exception as e:
        logger.error(f"Daily progress prompts job error: {e}", exc_info=True)


def start_scheduler(app):
    """
    Start the APScheduler background job.
    Called from main.py lifespan.
    """
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            send_due_notifications,
            "interval",
            minutes=5,
            id="schedule_notifications",
            replace_existing=True,
        )
        scheduler.add_job(
            send_daily_progress_prompts,
            "interval",
            minutes=60,
            id="daily_progress_prompts",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("APScheduler started — checking for due notifications every 5 minutes and daily progress prompts hourly")
        return scheduler
    except ImportError:
        logger.warning("APScheduler not installed — background notifications disabled. Run: pip install apscheduler")
        return None


def stop_scheduler(scheduler):
    """Gracefully shut down the scheduler"""
    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
