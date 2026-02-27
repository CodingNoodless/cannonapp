"""
Leaderboard API
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from db import get_database
from middleware import get_current_user
from middleware.auth_middleware import require_paid_user
from bson import ObjectId

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("")
async def get_leaderboard(limit: int = 100, current_user: dict = Depends(require_paid_user)):
    """Get leaderboard rankings"""
    db = get_database()
    cursor = db.leaderboard.find().sort("rank", 1).limit(limit)
    
    entries = []
    async for entry in cursor:
        user = await db.users.find_one({"_id": ObjectId(entry["user_id"])}) if entry.get("user_id") else None
        
        # Skip if user is admin (safety check in case they somehow got an entry)
        if user and user.get("is_admin"):
            continue
            
        entries.append({
            "rank": entry.get("rank", 0),
            "user_id": str(entry["user_id"]),
            "user_email": user["email"][:3] + "***" if user else "Anonymous",
            "score": entry.get("score", 0),
            "level": entry.get("level", 0),
            "streak_days": entry.get("streak_days", 0),
            "improvement_percentage": entry.get("improvement_percentage", 0)
        })
    
    total = len(entries) # Should ideally be count_documents excluding admins
    return {"entries": entries, "total_users": total}


@router.get("/me")
async def get_my_rank(current_user: dict = Depends(require_paid_user)):
    """Get current user's rank"""
    if current_user.get("is_admin"):
        return {"rank": None, "total_users": 0, "message": "Admins are excluded from leaderboard"}

    db = get_database()
    user_id = current_user["id"]
    entry = await db.leaderboard.find_one({"user_id": user_id})
    total = await db.leaderboard.count_documents({})
    
    # If no leaderboard entry, check if user has completed scans and create entry
    if not entry:
        latest_scan = await db.scans.find_one({
            "user_id": user_id,
            "processing_status": "completed",
            "analysis": {"$exists": True}
        }, sort=[("created_at", -1)])
        
        if latest_scan:
            # User has completed scan but no leaderboard entry - create one
            analysis = latest_scan.get("analysis", {})
            overall_score = analysis.get("overall_score") or analysis.get("metrics", {}).get("overall_score", 0)
            leaderboard_score = (float(overall_score) if overall_score else 0) * 10
            
            # Count scans
            scans_count = await db.scans.count_documents({
                "user_id": user_id,
                "processing_status": "completed"
            })
            
            # Create leaderboard entry
            new_entry = {
                "user_id": user_id,
                "score": leaderboard_score,
                "level": float(overall_score) if overall_score else 0,
                "streak_days": 1,
                "improvement_percentage": 0,
                "scans_count": scans_count,
                "last_scan_at": latest_scan.get("created_at", datetime.utcnow()),
                "created_at": datetime.utcnow()
            }
            await db.leaderboard.insert_one(new_entry)
            
            # Recalculate all ranks
            all_entries = await db.leaderboard.find().sort("score", -1).to_list(None)
            for rank, e in enumerate(all_entries, 1):
                await db.leaderboard.update_one({"_id": e["_id"]}, {"$set": {"rank": rank}})
            
            # Fetch the newly created entry with rank
            entry = await db.leaderboard.find_one({"user_id": user_id})
            total = await db.leaderboard.count_documents({})
        else:
            return {"rank": None, "total_users": total, "message": "Complete a scan to join"}
    
    return {
        "rank": entry.get("rank", 0),
        "total_users": total,
        "score": entry.get("score", 0),
        "level": entry.get("level", 0),
        "streak_days": entry.get("streak_days", 0),
        "improvement_percentage": entry.get("improvement_percentage", 0)
    }

