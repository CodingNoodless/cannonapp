"""
Admin API - Administrative management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from db import get_database
from middleware.auth_middleware import get_current_admin_user
from models.user import UserResponse

class BroadcastRequest(BaseModel):
    content: str

class DirectMessageRequest(BaseModel):
    user_id: str
    content: str

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    admin: dict = Depends(get_current_admin_user)
):
    """List all users with pagination and search (Admin only)"""
    db = get_database()
    
    query = {}
    if q:
        query["email"] = {"$regex": q, "$options": "i"}
        
    cursor = db.users.find(query).skip(skip).limit(limit).sort("created_at", -1)
    users = []
    async for user in cursor:
        user["id"] = str(user["_id"])
        users.append(user)
        
    return users

@router.get("/stats")
async def get_stats(admin: dict = Depends(get_current_admin_user)):
    """Get high-level system stats"""
    db = get_database()
    
    user_count = await db.users.count_documents({})
    paid_count = await db.users.count_documents({"is_paid": True})
    channel_count = await db.forums.count_documents({})
    message_count = await db.channel_messages.count_documents({})
    
    return {
        "total_users": user_count,
        "paid_users": paid_count,
        "total_channels": channel_count,
        "total_messages": message_count
    }

@router.post("/broadcast")
async def broadcast_message(
    data: BroadcastRequest,
    admin: dict = Depends(get_current_admin_user)
):
    """Send a message to ALL users in their Cannon AI chat"""
    db = get_database()
    
    cursor = db.users.find({}, {"_id": 1})
    count = 0
    async for user in cursor:
        user_id = str(user["_id"])
        new_msg = {
            "role": "assistant",
            "content": f"[BROADCAST] {data.content}",
            "created_at": datetime.utcnow()
        }
        history_doc = await db.chat_history.find_one({"user_id": user_id, "messages": {"$exists": True}})
        if history_doc:
            await db.chat_history.update_one(
                {"_id": history_doc["_id"]},
                {"$push": {"messages": new_msg}, "$set": {"updated_at": datetime.utcnow()}}
            )
        else:
            await db.chat_history.insert_one({
                "user_id": user_id,
                "messages": [new_msg],
                "created_at": datetime.utcnow()
            })
        count += 1
        
    return {"message": f"Broadcast sent to {count} users"}

@router.post("/direct")
async def direct_message(
    data: DirectMessageRequest,
    admin: dict = Depends(get_current_admin_user)
):
    """Send a direct message to a specific user as Cannon"""
    db = get_database()
    
    # Verify user exists
    target = await db.users.find_one({"_id": ObjectId(data.user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_msg = {
        "role": "assistant",
        "content": data.content,
        "created_at": datetime.utcnow()
    }
    
    history_doc = await db.chat_history.find_one({"user_id": data.user_id, "messages": {"$exists": True}})
    if history_doc:
        await db.chat_history.update_one(
            {"_id": history_doc["_id"]},
            {"$push": {"messages": new_msg}, "$set": {"updated_at": datetime.utcnow()}}
        )
    else:
        await db.chat_history.insert_one({
            "user_id": data.user_id,
            "messages": [new_msg],
            "created_at": datetime.utcnow()
        })
    
    return {"status": "Message sent"}


# ----- Admin ↔ User Chat (as Cannon) -----

class AdminChatMessage(BaseModel):
    message: str

@router.get("/users/{user_id}/chat")
async def get_user_chat(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    admin: dict = Depends(get_current_admin_user)
):
    """Get a user's Cannon chat history (admin only)"""
    db = get_database()

    # Verify user exists
    target = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    history_doc = await db.chat_history.find_one({"user_id": user_id, "messages": {"$exists": True}})
    messages = history_doc.get("messages", [])[-limit:] if history_doc else []
    return {
        "user_id": user_id,
        "email": target.get("email", ""),
        "messages": messages
    }

@router.post("/users/{user_id}/chat")
async def send_user_chat(
    user_id: str,
    data: AdminChatMessage,
    admin: dict = Depends(get_current_admin_user)
):
    """Send a message to a user's Cannon chat as the assistant (admin only)"""
    db = get_database()

    # Verify user exists
    target = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    new_msg = {
        "role": "assistant",
        "content": data.message,
        "created_at": datetime.utcnow()
    }

    history_doc = await db.chat_history.find_one({"user_id": user_id, "messages": {"$exists": True}})
    if history_doc:
        await db.chat_history.update_one(
            {"_id": history_doc["_id"]},
            {"$push": {"messages": new_msg}, "$set": {"updated_at": datetime.utcnow()}}
        )
    else:
        await db.chat_history.insert_one({
            "user_id": user_id,
            "messages": [new_msg],
            "created_at": datetime.utcnow()
        })

    return {"status": "Message sent", "message": new_msg}
