"""
Chat API - Max LLM Chat
Handles AI chat with tool-calling, coaching state, check-in parsing, and memory.
"""

import re
from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db import get_db, get_rds_db_optional
from middleware.auth_middleware import require_paid_user
from services.gemini_service import gemini_service
from services.storage_service import storage_service
from services.coaching_service import coaching_service
from models.leaderboard import ChatRequest, ChatResponse
from models.sqlalchemy_models import ChatHistory, Scan, User

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(
    data: ChatRequest,
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
    rds_db: AsyncSession | None = Depends(get_rds_db_optional),
):
    """Send message to Max AI"""
    from services.schedule_service import schedule_service
    user_id = current_user["id"]
    user_uuid = UUID(user_id)

    # Load chat history
    history_result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.user_id == user_uuid)
        .order_by(ChatHistory.created_at.desc())
        .limit(50)
    )
    history_rows = list(reversed(history_result.scalars().all()))
    history = [
        {"role": h.role, "content": h.content, "created_at": h.created_at}
        for h in history_rows
    ]

    # Build full coaching context (schedule, scans, state, memory, tone)
    coaching_context = await coaching_service.build_full_context(user_id, db, rds_db)

    active_schedule = await schedule_service.get_current_schedule(user_id, db=db)
    user = await db.get(User, user_uuid)
    onboarding = (user.onboarding if user else {}) or {}

    user_context = {
        "coaching_context": coaching_context,
        "active_schedule": active_schedule,
        "onboarding": onboarding,
    }

    # --- Init context / maxx schedule onboarding ---
    message = data.message
    maxx_id = data.init_context
    if not maxx_id and message:
        msg_lower = message.lower()
        if "skinmax" in msg_lower or "skin max" in msg_lower:
            maxx_id = "skinmax"
        elif "hairmax" in msg_lower or "hair max" in msg_lower:
            maxx_id = "hairmax"
        elif "fitmax" in msg_lower or "fit max" in msg_lower:
            maxx_id = "fitmax"

    # Fallback: if no init_context but user has no skinmax schedule and last assistant msg asked onboarding Qs, keep flow
    if not maxx_id:
        try:
            existing = await schedule_service.get_maxx_schedule(user_id, "skinmax", db=db)
            if not existing and history:
                last_assistant = next((h["content"] for h in reversed(history) if h.get("role") == "assistant"), "")
                last_lower = last_assistant.lower()
                # Only continue onboarding if the last message was clearly asking a specific setup question
                if any(p in last_lower for p in ("what time do you usually wake", "what time do you usually go to sleep", "gonna be outside today", "skin concern", "main skin concern", "skinmax schedule")):
                    maxx_id = "skinmax"
        except Exception:
            pass

    if maxx_id:
        try:
            existing_maxx = await schedule_service.get_maxx_schedule(user_id, maxx_id, db=db)
        except Exception:
            existing_maxx = None
        if existing_maxx:
            user_context["active_maxx_schedule"] = existing_maxx
            message = f"[SYSTEM: User opened {maxx_id} and already has an active schedule.]\n\n{message}"
        else:
            concern_question, concerns = None, []
            if rds_db:
                try:
                    from models.rds_models import Maxx
                    result = await rds_db.execute(select(Maxx).where(Maxx.id == maxx_id))
                    maxx_row = result.scalar_one_or_none()
                    if maxx_row and maxx_row.concern_question and maxx_row.concerns:
                        concern_question = maxx_row.concern_question
                        concerns = maxx_row.concerns or []
                except Exception:
                    pass
            if not concern_question or not concerns:
                from services.maxx_guidelines import MAXX_GUIDELINES
                fallback = MAXX_GUIDELINES.get(maxx_id)
                if fallback:
                    concern_question = fallback.get("concern_question")
                    concerns = fallback.get("concerns") or []

            if concern_question and concerns:
                concerns_str = ", ".join(c.get("label", c.get("id", "")) for c in concerns)
                message = f"""[SYSTEM: User wants to start their {maxx_id} schedule.

You need ALL 4 of these before you can generate the schedule:
  ☐ skin_concern (acne / pigmentation / texture / redness / aging)
  ☐ wake_time (in 24h format, e.g. "07:00")
  ☐ sleep_time (in 24h format, e.g. "23:00")
  ☐ outside_today (true / false)

FLOW — ask ONE thing per message, in this order:
1. First message: Greet briefly, explain the schedule, then ask their skin concern. Options: {concerns_str}.
2. They answer concern → Acknowledge briefly, then ask: "what time do you usually wake up?"
3. They answer wake time → Acknowledge briefly, then ask: "what time do you usually go to sleep?"
4. They answer sleep time → Acknowledge briefly, then ask: "last one — you gonna be outside today? need to know for sunscreen reminders"
5. They answer outside → NOW call generate_maxx_schedule(maxx_id="{maxx_id}", skin_concern=<mapped concern>, wake_time=<24h>, sleep_time=<24h>, outside_today=<bool>).

CRITICAL — DO NOT STOP EARLY:
- If you just got SLEEP TIME, you MUST ask "you gonna be outside today?" next. Do NOT just say "alright" and stop.
- If you just got OUTSIDE, you MUST call generate_maxx_schedule immediately. Do NOT stop.
- DO NOT generate the schedule until you have all 4 answers.
- After acknowledging an answer, ALWAYS ask the next question in the same message.

CONCERN MATCHING — map user's words to the closest concern ID:
- breakouts / pimples / oily / congestion / clogged pores → acne
- dark spots / uneven tone / hyperpigmentation / discoloration → pigmentation
- rough skin / scars / scarring / bumpy / uneven texture → texture
- redness / sensitive / irritation / rosacea / flushing → redness
- wrinkles / fine lines / aging / anti-aging / dull skin / skin quality → aging
Always pass the mapped ID, not raw text.]\n\n{message}"""
            else:
                message = f"""[SYSTEM: User wants to start {maxx_id} schedule. COMPOSE natural messages for each step:
1. Greet and explain the schedule. Then ask wake time in a natural way. Wait for answer.
2. Acknowledge their wake time, then ask sleep time. Wait for answer.
3. Acknowledge sleep time, then ask about outside today (for sunscreen reminders). Wait for answer.
4. Once you have wake_time, sleep_time, outside_today, call generate_maxx_schedule.
Each message: acknowledge their last answer, then ask the next question. ONE question per message.]\n\n{message}"""

    # --- Image handling ---
    image_data = None
    if data.attachment_url and data.attachment_type == "image":
        image_data = await storage_service.get_image(data.attachment_url)

    # --- LLM call (retry once on failure) ---
    result = None
    for _attempt in range(2):
        try:
            result = await gemini_service.chat(message, history, user_context, image_data)
            if result:
                break
        except Exception as _llm_err:
            print(f"LLM attempt {_attempt + 1} failed: {_llm_err}")
            if _attempt == 1:
                result = {"text": "my bad, hit a snag. try again real quick.", "tool_calls": []}
    result = result or {"text": "my bad, hit a snag. try again real quick.", "tool_calls": []}
    response_text = result.get("text", "")
    tool_calls = result.get("tool_calls", [])

    # --- Process tool calls ---
    schedule_for_tools = active_schedule or await schedule_service.get_maxx_schedule(user_id, "skinmax", db=db)
    for tool in tool_calls:
        if tool["name"] == "modify_schedule" and schedule_for_tools:
            try:
                feedback = tool["args"].get("feedback")
                if feedback:
                    await schedule_service.adapt_schedule(
                        user_id=user_id,
                        schedule_id=schedule_for_tools["id"],
                        db=db,
                        feedback=feedback,
                    )
            except Exception as e:
                print(f"Schedule adaptation failed: {e}")

        elif tool["name"] == "generate_maxx_schedule":
            try:
                import asyncio
                args = tool["args"]
                skin_concern = args.get("skin_concern") or onboarding.get("skin_type")
                # Fuzzy-match concern to valid key if AI passed raw text
                if skin_concern and skin_concern not in ("acne", "pigmentation", "texture", "redness", "aging"):
                    from services.skinmax import get_concern_key
                    matched = get_concern_key(skin_concern)
                    if matched:
                        skin_concern = matched
                # Show a holding message while the schedule generates
                if not response_text.strip():
                    response_text = "alright, locking in your schedule now — give me a sec..."
                schedule = await asyncio.wait_for(
                    schedule_service.generate_maxx_schedule(
                        user_id=user_id,
                        maxx_id=str(args.get("maxx_id", "skinmax")),
                        db=db,
                        rds_db=rds_db if rds_db else None,
                        wake_time=str(args.get("wake_time", "07:00")),
                        sleep_time=str(args.get("sleep_time", "23:00")),
                        skin_concern=skin_concern,
                        outside_today=bool(args.get("outside_today", False)),
                    ),
                    timeout=60,
                )
                schedule_summary = _summarise_schedule(schedule)
                # Replace the placeholder with the real schedule
                response_text = schedule_summary
            except asyncio.TimeoutError:
                print("Maxx schedule generation timed out")
                response_text = "took too long to build your schedule — hit me again and i'll set it up."
            except Exception as e:
                print(f"Maxx schedule generation failed: {e}")
                response_text = "had some trouble building your schedule. try again in a sec."

        elif tool["name"] == "update_schedule_context":
            try:
                args = tool["args"]
                key, value = str(args.get("key", "")), str(args.get("value", ""))
                if not key:
                    continue
                if schedule_for_tools:
                    await schedule_service.update_schedule_context(
                        user_id=user_id,
                        schedule_id=schedule_for_tools["id"],
                        db=db,
                        context_updates={key: value},
                    )
                else:
                    user_obj = await db.get(User, user_uuid)
                    if user_obj:
                        prefs = dict(user_obj.schedule_preferences or {})
                        prefs[key] = value
                        user_obj.schedule_preferences = prefs
                        await db.commit()
            except Exception as e:
                print(f"Context update failed: {e}")

        elif tool["name"] == "log_check_in":
            try:
                args = tool["args"]
                check_in_data = {}
                if args.get("workout_done"):
                    check_in_data["workout_done"] = True
                if args.get("missed"):
                    check_in_data["missed"] = True
                if args.get("sleep_hours"):
                    check_in_data["sleep_hours"] = args["sleep_hours"]
                if args.get("calories"):
                    check_in_data["calories"] = args["calories"]
                if args.get("mood"):
                    check_in_data["mood"] = args["mood"]
                if args.get("injury_area"):
                    check_in_data["injury"] = {
                        "area": args["injury_area"],
                        "note": args.get("injury_note", ""),
                    }
                if check_in_data:
                    await coaching_service.process_check_in(user_id, db, check_in_data)
            except Exception as e:
                print(f"Check-in logging failed: {e}")

    # --- Fallback: user said wake/sleep time but got wrong response — parse and update schedule ---
    # Skip during onboarding (maxx_id set + no existing schedule) — let the AI handle it sequentially
    msg = data.message or ""
    msg_lower = msg.lower()
    in_onboarding = bool(maxx_id and not (user_context.get("active_maxx_schedule")))
    if not in_onboarding:
        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", msg_lower, re.I)
        is_wake = any(p in msg_lower for p in ("waking up at", "wake up at", "wake at", "waking at", "imma be waking", "gonna wake", "waking up at like"))
        is_sleep = any(p in msg_lower for p in ("sleep at", "sleeping at", "bed at", "going to bed at", "boutta sleep at"))
        if (is_wake or is_sleep) and time_match and schedule_for_tools:
            hour, minute = int(time_match.group(1)), int(time_match.group(2) or "0")
            ampm = (time_match.group(3) or "am" if is_wake else "pm").lower()
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            time_24 = f"{hour:02d}:{minute:02d}"
            key = "wake_time" if is_wake else "sleep_time"
            schedule_updated = False
            try:
                await schedule_service.update_schedule_context(user_id=user_id, schedule_id=schedule_for_tools["id"], db=db, context_updates={key: time_24})
                fb = f"User wakes at {time_24}. Shift AM tasks to start after {time_24}." if is_wake else f"User sleeps at {time_24}. PM routine 1hr before."
                await schedule_service.adapt_schedule(user_id=user_id, schedule_id=schedule_for_tools["id"], db=db, feedback=fb)
                schedule_updated = True
            except Exception:
                pass
            # If we had to update (AI didn't), get AI to generate proper reply
            if schedule_updated and not any(w in response_text.lower() for w in ("update", "schedule", "gotchu", "on it", "locked in")):
                ctx = f"You just updated their schedule ({'wake' if is_wake else 'sleep'} at {time_24})."
                new_reply = gemini_service.generate_brief_reply(msg, ctx)
                if new_reply:
                    response_text = new_reply

        # --- Fallback: user said going outside — update context only, don't override AI response ---
        if any(p in msg_lower for p in ("going outside", "going out", "outside today", "beach", "headed out", "gonna be outside")):
            if schedule_for_tools:
                try:
                    await schedule_service.update_schedule_context(
                        user_id=user_id,
                        schedule_id=schedule_for_tools["id"],
                        db=db,
                        context_updates={"outside_today": "true"},
                    )
                except Exception:
                    pass
            # Don't override — AI should know what to say

    # --- Enforce lowercase on all AI responses ---
    response_text = response_text.lower()

    # --- Save messages ---
    now = datetime.utcnow()
    user_message = ChatHistory(
        user_id=user_uuid,
        role="user",
        content=data.message,
        created_at=now,
    )
    assistant_message = ChatHistory(
        user_id=user_uuid,
        role="assistant",
        content=response_text,
        created_at=now + timedelta(milliseconds=1),
    )
    db.add(user_message)
    db.add(assistant_message)
    await db.commit()

    # --- Background: update AI memory every ~10 messages ---
    total_msgs = len(history) + 2
    if total_msgs % 10 == 0:
        try:
            summary = await coaching_service.generate_conversation_summary(history[-20:])
            if summary:
                await coaching_service.update_ai_memory(user_id, db, summary)
        except Exception as e:
            print(f"AI memory update failed: {e}")

    # --- Background: detect tone preference every ~20 messages ---
    if total_msgs % 20 == 0:
        try:
            await coaching_service.detect_tone_preference(user_id, db, history[-30:])
        except Exception as e:
            print(f"Tone detection failed: {e}")

    return ChatResponse(response=response_text)


@router.post("/trigger-check-in")
async def trigger_check_in(
    check_in_type: str = "midday",
    missed_today: int = 0,
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
    rds_db: AsyncSession | None = Depends(get_rds_db_optional),
):
    """
    Trigger a check-in message immediately (for testing).
    Bypasses time and cooldown checks. Sends an AI-generated check-in to the current user.
    Types: morning, midday, night, missed_task, weekly
    """
    user_id = current_user["id"]
    user_uuid = UUID(user_id)

    msg_text = await coaching_service.generate_check_in_message(
        user_id, db, rds_db, check_in_type, missed_today
    )

    chat_msg = ChatHistory(
        user_id=user_uuid,
        role="assistant",
        content=msg_text,
        created_at=datetime.utcnow(),
    )
    db.add(chat_msg)
    await db.commit()

    return {"message": msg_text, "check_in_type": check_in_type}


@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    current_user: dict = Depends(require_paid_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chat history"""
    user_uuid = UUID(current_user["id"])
    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.user_id == user_uuid)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
    )
    rows = list(reversed(result.scalars().all()))
    return {
        "messages": [
            {"role": r.role, "content": r.content, "created_at": r.created_at}
            for r in rows
        ]
    }


def _summarise_schedule(schedule: dict) -> str:
    """Build a short summary of a generated schedule."""
    days = schedule.get("days", [])
    if not days:
        return "schedule created. stay on track 💪"

    first_day = days[0]
    tasks = first_day.get("tasks", [])
    lines = [f"your {schedule.get('course_title', 'schedule')} is locked in. day 1:"]
    for t in tasks[:5]:
        lines.append(f"  {t.get('time', '??:??')} — {t.get('title', 'Task')}")
    if len(tasks) > 5:
        lines.append(f"  +{len(tasks) - 5} more")
    lines.append(f"\n{len(days)} days planned. stay on it.")
    return "\n".join(lines)
