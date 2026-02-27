from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from datetime import datetime
from bson import ObjectId
from db import get_database
from middleware import get_current_user
from middleware.auth_middleware import require_paid_user
from services.storage_service import storage_service
from services.facial_analysis_client import facial_analysis_client

router = APIRouter(prefix="/scans", tags=["Face Scans"])


@router.post("/upload-video")
async def upload_scan_video(
    video: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a 15-second face scan video"""
    db = get_database()
    user_id = current_user["id"]
    
    video_data = await video.read()
    video_url = await storage_service.upload_video(video_data, user_id)
    
    if not video_url:
        raise HTTPException(status_code=500, detail="Failed to upload video")
    
    scan_doc = {
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "video_url": video_url,
        "is_unlocked": current_user.get("is_paid", False),
        "processing_status": "pending",
        "scan_type": "video"
    }
    
    result = await db.scans.insert_one(scan_doc)
    scan_id = str(result.inserted_id)
    
    if not current_user.get("first_scan_completed", False):
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"first_scan_completed": True}}
        )
    
    return {"scan_id": scan_id, "video_url": video_url}


@router.post("/{scan_id}/analyze")
async def analyze_scan(scan_id: str, current_user: dict = Depends(get_current_user)):
    """Trigger AI analysis for uploaded scan (supports both image and video)"""
    db = get_database()
    
    scan = await db.scans.find_one({"_id": ObjectId(scan_id), "user_id": current_user["id"]})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    await db.scans.update_one({"_id": ObjectId(scan_id)}, {"$set": {"processing_status": "processing"}})
    
    try:
        # Handle video scan
        if scan.get("scan_type") == "video":
            video_url = scan["video_url"]
            if video_url.startswith("/uploads/"):
                video_data = await storage_service.get_image(video_url) # get_image works for any file
            else:
                import httpx
                async with httpx.AsyncClient() as client:
                    resp = await client.get(video_url)
                    video_data = resp.content
            
            if not video_data:
                raise HTTPException(status_code=500, detail="Failed to retrieve video data")
            
            # Send video directly to cannon_facial_analysis service
            analysis = await facial_analysis_client.upload_video(video_data)
        else:
            # Handle legacy image scan
            front_url = scan["images"]["front"]
            left_url = scan["images"]["left"]
            right_url = scan["images"]["right"]
            
            if front_url.startswith("/uploads/"):
                front_data = await storage_service.get_image(front_url)
                left_data = await storage_service.get_image(left_url)
                right_data = await storage_service.get_image(right_url)
            else:
                import httpx
                async with httpx.AsyncClient() as client:
                    front_resp = await client.get(front_url)
                    left_resp = await client.get(left_url)
                    right_resp = await client.get(right_url)
                front_data = front_resp.content
                left_data = left_resp.content
                right_data = right_resp.content
            
            if not all([front_data, left_data, right_data]):
                raise HTTPException(status_code=500, detail="Failed to retrieve images")
            
            analysis = await facial_analysis_client.analyze_frames([front_data, left_data, right_data])
        
        await db.scans.update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": {"analysis": analysis, "processing_status": "completed"}}
        )
        
        # Update leaderboard entry for this user
        user_id = current_user["id"]
        
        overall_score = 0.0
        if isinstance(analysis, dict):
            # Try new format first, then old format
            overall_score = analysis.get("scan_summary", {}).get("overall_score")
            if overall_score is None:
                overall_score = analysis.get("metrics", {}).get("overall_score")
            if overall_score is None:
                overall_score = analysis.get("overall_score", 0.0)
        elif hasattr(analysis, "overall_score"):
            overall_score = getattr(analysis, "overall_score")
        elif hasattr(analysis, "metrics") and hasattr(analysis.metrics, "overall_score"):
            overall_score = getattr(analysis.metrics, "overall_score")
        
        # Get all completed scans for this user to calculate improvement
        scan_cursor = db.scans.find({
            "user_id": user_id,
            "processing_status": "completed",
            "analysis": {"$exists": True}
        }).sort("created_at", -1)
        
        user_scans = []
        async for s in scan_cursor:
            a = s.get("analysis", {})
            score = a.get("scan_summary", {}).get("overall_score")
            if score is None:
                score = a.get("metrics", {}).get("overall_score")
            if score is None:
                score = a.get("overall_score", 0)
            user_scans.append({"score": score, "created_at": s.get("created_at")})
        
        # Calculate improvement percentage (compare first to latest)
        improvement_percentage = 0
        if len(user_scans) >= 2:
            first_score = user_scans[-1]["score"] or 0
            latest_score = user_scans[0]["score"] or 0
            if first_score > 0:
                improvement_percentage = ((latest_score - first_score) / first_score) * 100
        
        # Calculate score for leaderboard (based on overall_score * multiplier)
        leaderboard_score = (float(overall_score) if overall_score else 0) * 10  # Scale to 100
        
        # Update or create leaderboard entry
        existing_entry = await db.leaderboard.find_one({"user_id": user_id})
        
        if existing_entry:
            # Update with new score if higher
            new_score = max(existing_entry.get("score", 0), leaderboard_score)
            await db.leaderboard.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "score": new_score,
                        "level": float(overall_score) if overall_score else 0,
                        "improvement_percentage": improvement_percentage,
                        "last_scan_at": datetime.utcnow()
                    },
                    "$inc": {"scans_count": 1}
                }
            )
        else:
            # Create new entry
            await db.leaderboard.insert_one({
                "user_id": user_id,
                "score": leaderboard_score,
                "level": float(overall_score) if overall_score else 0,
                "streak_days": 1,
                "improvement_percentage": 0,
                "scans_count": 1,
                "last_scan_at": datetime.utcnow(),
                "created_at": datetime.utcnow()
            })
        
        # Recalculate ranks for all leaderboard entries
        all_entries = await db.leaderboard.find().sort("score", -1).to_list(None)
        for rank, entry in enumerate(all_entries, 1):
            await db.leaderboard.update_one({"_id": entry["_id"]}, {"$set": {"rank": rank}})
        
        return {"message": "Analysis complete", "scan_id": scan_id}
    except Exception as e:
        await db.scans.update_one({"_id": ObjectId(scan_id)}, {"$set": {"processing_status": "failed", "error_message": str(e)}})
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


@router.get("/latest")
async def get_latest_scan(current_user: dict = Depends(get_current_user)):
    """Get most recent scan"""
    db = get_database()
    scan = await db.scans.find_one({"user_id": current_user["id"]}, sort=[("created_at", -1)])
    if not scan:
        raise HTTPException(status_code=404, detail="No scans found")
    
    is_paid = current_user.get("is_paid", False)
    response = {
        "id": str(scan["_id"]),
        "created_at": scan["created_at"],
        "images": scan.get("images", {}),
        "is_unlocked": is_paid,
        "processing_status": scan.get("processing_status")
    }
    
    if scan.get("analysis"):
        if is_paid:
            response["analysis"] = scan["analysis"]
        else:
            # For unpaid users, only show overall score
            a = scan["analysis"]
            overall_score = a.get("scan_summary", {}).get("overall_score")
            if overall_score is None:
                overall_score = a.get("metrics", {}).get("overall_score")
            if overall_score is None:
                overall_score = a.get("overall_score", 0)
            response["analysis"] = {"overall_score": overall_score, "locked": True}
    
    return response


@router.get("/history")
async def get_scan_history(limit: int = 10, current_user: dict = Depends(require_paid_user)):
    """Get scan history (paid only)"""
    db = get_database()
    cursor = db.scans.find({"user_id": current_user["id"]}).sort("created_at", -1).limit(limit)
    scans = []
    async for s in cursor:
        a = s.get("analysis", {})
        score = a.get("scan_summary", {}).get("overall_score")
        if score is None:
            score = a.get("metrics", {}).get("overall_score")
        if score is None:
            score = a.get("overall_score", 0)
        scans.append({"id": str(s["_id"]), "created_at": s["created_at"], "overall_score": score})
    return {"scans": scans}


@router.get("/{scan_id}")
async def get_scan_by_id(scan_id: str, current_user: dict = Depends(require_paid_user)):
    """Get a specific scan with full analysis (paid only)"""
    db = get_database()
    
    scan = await db.scans.find_one({"_id": ObjectId(scan_id), "user_id": current_user["id"]})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return {
        "id": str(scan["_id"]),
        "created_at": scan["created_at"],
        "images": scan.get("images", {}),
        "analysis": scan.get("analysis"),
        "processing_status": scan.get("processing_status")
    }

