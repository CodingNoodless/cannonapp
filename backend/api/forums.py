"""
Channels API - Discord-like chat channels
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from datetime import datetime
from bson import ObjectId
from db import get_database
from middleware import get_current_user
from middleware.auth_middleware import require_paid_user, get_current_admin_user
from models.forum import ChannelCreate, MessageCreate
from services.storage_service import storage_service

router = APIRouter(prefix="/forums", tags=["Channels"])


@router.post("/upload")
async def upload_chat_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_paid_user)
):
    """Upload a file or image for chat attachment"""
    file_data = await file.read()
    user_id = current_user["id"]
    
    # Use storage service (legacy upload_image for now as it handles byte data)
    file_url = await storage_service.upload_image(file_data, user_id, "chat")
    
    if not file_url:
        raise HTTPException(status_code=500, detail="Failed to upload file")
        
    return {"url": file_url}


@router.get("")
# ... (list_channels code)
async def list_channels(q: str = None, current_user: dict = Depends(require_paid_user)):
    """List all channels with optional search"""
    db = get_database()
    
    query = {}
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"slug": {"$regex": q, "$options": "i"}}
        ]
        
    cursor = db.forums.find(query).sort("order", 1)
    channels = []
    async for ch in cursor:
        message_count = await db.channel_messages.count_documents({"channel_id": str(ch["_id"])})
        channels.append({
            "id": str(ch["_id"]),
            "name": ch["name"],
            "slug": ch["slug"],
            "description": ch["description"],
            "is_admin_only": ch.get("is_admin_only", False),
            "message_count": message_count
        })
    return {"forums": channels}


@router.get("/{channel_id}/messages")
async def get_messages(channel_id: str, limit: int = 50, before: str = None, query: str = None, current_user: dict = Depends(require_paid_user)):
    """Get messages in a channel with optional filtering"""
    db = get_database()
    
    channel = await db.forums.find_one({"_id": ObjectId(channel_id)})
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    mq = {"channel_id": channel_id}
    if before:
        mq["_id"] = {"$lt": ObjectId(before)}
    if query:
        mq["content"] = {"$regex": query, "$options": "i"}
    
    cursor = db.channel_messages.find(mq).sort("created_at", 1).limit(limit)
    
    messages = []
    async for msg in cursor:
        user = await db.users.find_one({"_id": ObjectId(msg["user_id"])})
        messages.append({
            "id": str(msg["_id"]),
            "channel_id": channel_id,
            "user_id": msg["user_id"],
            "user_email": user["email"].split("@")[0] if user else "Unknown",
            "content": msg["content"],
            "attachment_url": msg.get("attachment_url"),
            "attachment_type": msg.get("attachment_type"),
            "created_at": msg["created_at"],
            "is_admin": user.get("is_admin", False) if user else False,
            "parent_id": msg.get("parent_id"),
            "reactions": msg.get("reactions", {})
        })
    
    return {"messages": messages, "channel_name": channel["name"], "is_admin_only": channel.get("is_admin_only", False)}


@router.post("/{channel_id}/messages")
async def send_message(channel_id: str, data: MessageCreate, current_user: dict = Depends(require_paid_user)):
    """Send a message to a channel"""
    db = get_database()
    
    channel = await db.forums.find_one({"_id": ObjectId(channel_id)})
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check admin-only permission for TOP-LEVEL messages only
    if channel.get("is_admin_only") and not current_user.get("is_admin") and not data.parent_id:
        raise HTTPException(status_code=403, detail="Only admins can post announcements. You can still comment on them!")
    
    # Create message
    message = {
        "channel_id": channel_id,
        "user_id": current_user["id"],
        "content": data.content,
        "attachment_url": data.attachment_url,
        "attachment_type": data.attachment_type,
        "parent_id": data.parent_id,
        "reactions": {},
        "created_at": datetime.utcnow()
    }
    result = await db.channel_messages.insert_one(message)
    
    user = await db.users.find_one({"_id": ObjectId(current_user["id"])})
    
    return {
        "message": {
            "id": str(result.inserted_id),
            "channel_id": channel_id,
            "user_id": current_user["id"],
            "user_email": user["email"].split("@")[0] if user else "Unknown",
            "content": data.content,
            "attachment_url": data.attachment_url,
            "attachment_type": data.attachment_type,
            "parent_id": data.parent_id,
            "reactions": {},
            "created_at": message["created_at"],
            "is_admin": current_user.get("is_admin", False)
        }
    }


@router.post("/{channel_id}/messages/{message_id}/reactions")
async def toggle_reaction(channel_id: str, message_id: str, emoji: str, current_user: dict = Depends(require_paid_user)):
    """Add or remove an emoji reaction to a message"""
    db = get_database()
    user_id = current_user["id"]
    
    message = await db.channel_messages.find_one({"_id": ObjectId(message_id)})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    reactions = message.get("reactions", {})
    if emoji not in reactions:
        reactions[emoji] = []
    
    if user_id in reactions[emoji]:
        reactions[emoji].remove(user_id)
        if not reactions[emoji]:
            del reactions[emoji]
    else:
        reactions[emoji].append(user_id)
    
    await db.channel_messages.update_one(
        {"_id": ObjectId(message_id)},
        {"$set": {"reactions": reactions}}
    )
    
    return {"reactions": reactions}


@router.post("")
async def create_channel(data: ChannelCreate, admin: dict = Depends(get_current_admin_user)):
    """Create channel (admin only)"""
    db = get_database()
    channel = data.model_dump()
    channel["created_at"] = datetime.utcnow()
    result = await db.forums.insert_one(channel)
    return {"channel_id": str(result.inserted_id)}

