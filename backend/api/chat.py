"""
Chat API - Cannon LLM Chat
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db import get_db
from middleware.auth_middleware import require_paid_user
from services.gemini_service import gemini_service
from services.storage_service import storage_service
from services.skinmax import SKINMAX_CONCERNS, parse_time_from_text, get_concern_key
from models.leaderboard import ChatRequest, ChatResponse
from models.sqlalchemy_models import ChatHistory, Scan, User

router = APIRouter(prefix="/chat", tags=["Chat"])

def _user_tz(user: User) -> ZoneInfo:
    tz_name = (user.onboarding or {}).get("timezone", "UTC")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("UTC")


def _skinmax_prompt_for_concern() -> str:
    return (
        "Which skin concern should we focus on? Reply with a number:\n"
        "1) Acne / Congestion\n"
        "2) Pigmentation / Uneven Tone\n"
        "3) Texture / Scarring\n"
        "4) Redness / Sensitivity\n"
        "5) Aging / Skin Quality"
    )


def _skinmax_summary(concern_key: str, wake_time: str, sleep_time: str) -> str:
    concern = SKINMAX_CONCERNS[concern_key]
    return (
        "Skinmax reminders are set.\n\n"
        f"AM routine ({wake_time}): {concern['am']}\n"
        f"PM routine (1 hour before bed): {concern['pm']}\n"
        f"Weekly care: {concern['weekly']}\n"
        f"Sunscreen: {concern['sunscreen']}\n\n"
        "I’ll message you at wake time and 1 hour before sleep, plus sunscreen reapply every 3 hours.\n"
        "If you wake earlier or later, text me \"im awake\" so I can adjust."
    )


async def _handle_skinmax_flow(message: str, user: User) -> tuple[str | None, bool]:
    prefs = dict(user.schedule_preferences or {})
    skin = dict(prefs.get("skinmax") or {})
    msg = (message or "").strip()
    msg_lower = msg.lower()
    updated = False

    if skin.get("enabled") and skin.get("setup_complete"):
        if msg_lower in {"im awake", "i'm awake", "im up", "i am awake", "awake"}:
            tz = _user_tz(user)
            local_now = datetime.now(tz)
            skin["wake_time"] = local_now.strftime("%H:%M")
            skin["last_wake_reported_at"] = local_now.isoformat()
            last_sent = dict(skin.get("last_sent") or {})
            if last_sent.get("date") == local_now.date().isoformat():
                last_sent["am_sent"] = False
                last_sent["sunscreen_times"] = []
            skin["last_sent"] = last_sent
            prefs["skinmax"] = skin
            user.schedule_preferences = prefs
            updated = True
            return "Got it. You’re up. I’ll adjust today’s reminders.", updated
        # Intent: change wake/sleep time
        if "wake" in msg_lower and ("change" in msg_lower or "set" in msg_lower or "update" in msg_lower):
            new_time = parse_time_from_text(msg, default_meridian="am")
            if not new_time:
                return "What time should I set your wake time to?", False
            skin["wake_time"] = new_time
            prefs["skinmax"] = skin
            user.schedule_preferences = prefs
            updated = True
            return f"Updated your wake time to {new_time}.", updated
        if "sleep" in msg_lower or "bed" in msg_lower or "bedtime" in msg_lower:
            if "change" in msg_lower or "set" in msg_lower or "update" in msg_lower:
                new_time = parse_time_from_text(msg, default_meridian="pm")
                if not new_time:
                    return "What time should I set your bedtime to?", False
                skin["sleep_time"] = new_time
                prefs["skinmax"] = skin
                user.schedule_preferences = prefs
                updated = True
                return f"Updated your bedtime to {new_time}.", updated
        # Intent: show current reminders
        if "reminder" in msg_lower or "schedule" in msg_lower or "set to" in msg_lower:
            concern_key = skin.get("concern", "acne")
            return _skinmax_summary(concern_key, skin.get("wake_time", "07:00"), skin.get("sleep_time", "23:00")), False
        # Intent: change concern
        if "concern" in msg_lower or "switch" in msg_lower or "change" in msg_lower:
            concern_key = get_concern_key(msg_lower)
            if concern_key:
                skin["concern"] = concern_key
                prefs["skinmax"] = skin
                user.schedule_preferences = prefs
                updated = True
                return _skinmax_summary(concern_key, skin.get("wake_time", "07:00"), skin.get("sleep_time", "23:00")), updated
        return None, False

    step = skin.get("setup_step")
    if not step:
        skin["setup_step"] = "awaiting_wake_time"
        skin["enabled"] = True
        prefs["skinmax"] = skin
        user.schedule_preferences = prefs
        updated = True
        return "Let’s set your Skinmax reminders. What time do you usually wake up? (e.g. 7:30 AM)", updated

    if step == "awaiting_wake_time":
        wake_time = parse_time_from_text(msg, default_meridian="am")
        if not wake_time:
            return "What time do you usually wake up? Example: 7:00 AM or 6:30.", False
        skin["wake_time"] = wake_time
        skin["setup_step"] = "awaiting_sleep_time"
        prefs["skinmax"] = skin
        user.schedule_preferences = prefs
        updated = True
        return "Got it. What time do you usually go to sleep? (e.g. 10:30 PM)", updated

    if step == "awaiting_sleep_time":
        sleep_time = parse_time_from_text(msg, default_meridian="pm")
        if not sleep_time:
            return "What time do you usually go to sleep? Example: 10:30 PM or 11:00.", False
        skin["sleep_time"] = sleep_time
        skin["setup_step"] = "awaiting_concern"
        prefs["skinmax"] = skin
        user.schedule_preferences = prefs
        updated = True
        return _skinmax_prompt_for_concern(), updated

    if step == "awaiting_concern":
        # If user gave multiple options, ask to pick one
        if any(sep in msg_lower for sep in [" and ", ",", "/"]):
            return "Pick the single most important concern for now. Reply with one number (1-5).", False
        concern_key = get_concern_key(msg_lower)
        if not concern_key:
            return _skinmax_prompt_for_concern(), False
        skin["concern"] = concern_key
        skin["setup_step"] = None
        skin["setup_complete"] = True
        skin["enabled"] = True
        skin.setdefault("last_sent", {})
        prefs["skinmax"] = skin
        user.schedule_preferences = prefs
        updated = True
        return _skinmax_summary(concern_key, skin.get("wake_time", "07:00"), skin.get("sleep_time", "23:00")), updated

    return None, False


@router.post("/message", response_model=ChatResponse)
async def send_message(
    data: ChatRequest,
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    """Send message to Cannon AI"""
    from services.schedule_service import schedule_service
    user_id = current_user["id"]
    user_uuid = UUID(user_id)
    user = await db.get(User, user_uuid)

    # Skinmax setup / wake-time update flow (SMS-like)
    if user:
        skinmax_response, prefs_updated = await _handle_skinmax_flow(data.message, user)
        if skinmax_response:
            if prefs_updated:
                user.updated_at = datetime.utcnow()
            user_message = ChatHistory(
                user_id=user_uuid,
                role="user",
                content=data.message,
                created_at=datetime.utcnow()
            )
            assistant_message = ChatHistory(
                user_id=user_uuid,
                role="assistant",
                content=skinmax_response,
                created_at=datetime.utcnow()
            )
            db.add(user_message)
            db.add(assistant_message)
            await db.commit()
            return ChatResponse(response=skinmax_response)
    
    # Get chat history
    history_result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.user_id == user_uuid)
        .order_by(ChatHistory.created_at.desc())
        .limit(50)
    )
    history_rows = list(reversed(history_result.scalars().all()))
    history = [
        {
            "role": h.role,
            "content": h.content,
            "attachment_url": None,
            "attachment_type": None,
            "created_at": h.created_at
        }
        for h in history_rows
    ]
    
    # Get active schedule for context
    active_schedule = await schedule_service.get_current_schedule(user_id, db=db)
    
    # Get user context
    latest_scan_result = await db.execute(
        select(Scan).where(Scan.user_id == user_uuid).order_by(Scan.created_at.desc()).limit(1)
    )
    latest_scan = latest_scan_result.scalar_one_or_none()
    user_context = {
        "latest_scan": latest_scan.analysis if latest_scan else None,
        "active_schedule": active_schedule
    }
    
    # Get attachment data if it's an image
    image_data = None
    if data.attachment_url and data.attachment_type == "image":
        image_data = await storage_service.get_image(data.attachment_url)
    
    # Get response from Gemini
    result = await gemini_service.chat(data.message, history, user_context, image_data)
    response_text = result.get("text", "")
    tool_calls = result.get("tool_calls", [])
    
    # Handle tools
    for tool in tool_calls:
        if tool["name"] == "modify_schedule" and active_schedule:
            try:
                feedback = tool["args"].get("feedback")
                if feedback:
                    await schedule_service.adapt_schedule(
                        user_id=user_id,
                        schedule_id=active_schedule["id"],
                        db=db,
                        feedback=feedback
                    )
                    # We could optionally add a notice to the response or refresh the context
            except Exception as e:
                print(f"Chat-triggered schedule adaptation failed: {e}")
    
    # Save to history
    user_message = ChatHistory(
        user_id=user_uuid,
        role="user",
        content=data.message,
        created_at=datetime.utcnow()
    )
    assistant_message = ChatHistory(
        user_id=user_uuid,
        role="assistant",
        content=response_text,
        created_at=datetime.utcnow()
    )
    db.add(user_message)
    db.add(assistant_message)
    await db.commit()
    
    return ChatResponse(response=response_text)


@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chat history"""
    user_uuid = UUID(current_user["id"])
    # If user wants skinmax and hasn't set it up, seed the conversation
    user = await db.get(User, user_uuid)
    goals = (user.onboarding or {}).get("goals", []) if user else []
    skin = (user.schedule_preferences or {}).get("skinmax", {}) if user else {}

    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.user_id == user_uuid)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
    )
    rows = list(reversed(result.scalars().all()))

    should_seed = (
        user
        and "skinmax" in goals
        and not skin.get("setup_complete")
        and len(rows) == 0
    )
    if should_seed:
        prompt = "Let’s set your Skinmax reminders. What time do you usually wake up? (e.g. 7:30 AM)"
        assistant_message = ChatHistory(
            user_id=user_uuid,
            role="assistant",
            content=prompt,
            created_at=datetime.utcnow()
        )
        db.add(assistant_message)
        await db.commit()
        rows = [assistant_message]

    return {"messages": [
        {"role": r.role, "content": r.content, "created_at": r.created_at}
        for r in rows
    ]}
