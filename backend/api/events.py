"""
Events API - TikTok Live events
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from bson import ObjectId
from db import get_database
from middleware import get_current_user
from middleware.auth_middleware import require_paid_user, get_current_admin_user
from models.event import EventCreate

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("")
async def list_events(current_user: dict = Depends(require_paid_user)):
    """List upcoming events"""
    db = get_database()
    cursor = db.events.find({"scheduled_at": {"$gte": datetime.utcnow()}}).sort("scheduled_at", 1).limit(20)
    events = []
    async for e in cursor:
        e["id"] = str(e["_id"])
        del e["_id"]
        e["is_past"] = False
        events.append(e)
    return {"events": events}


@router.get("/live")
async def get_live_events(current_user: dict = Depends(require_paid_user)):
    """Get currently live events"""
    db = get_database()
    cursor = db.events.find({"is_live": True})
    events = [{"id": str(e["_id"]), "title": e["title"], "tiktok_link": e["tiktok_link"]} async for e in cursor]
    return {"events": events}


@router.get("/calendar")
async def get_calendar(month: int = None, year: int = None, current_user: dict = Depends(require_paid_user)):
    """Get events for calendar view"""
    db = get_database()
    now = datetime.utcnow()
    month = month or now.month
    year = year or now.year
    
    start = datetime(year, month, 1)
    end = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    
    cursor = db.events.find({"scheduled_at": {"$gte": start, "$lt": end}}).sort("scheduled_at", 1)
    events = [{"id": str(e["_id"]), "title": e["title"], "scheduled_at": e["scheduled_at"], "duration_minutes": e.get("duration_minutes", 60)} async for e in cursor]
    return {"events": events, "month": month, "year": year}


@router.post("")
async def create_event(data: EventCreate, admin: dict = Depends(get_current_admin_user)):
    """Create event (admin only)"""
    db = get_database()
    event = data.model_dump()
    event["created_at"] = datetime.utcnow()
    event["is_live"] = False
    result = await db.events.insert_one(event)
    return {"event_id": str(result.inserted_id)}
