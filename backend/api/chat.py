"""
Chat API - Cannon LLM Chat
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from bson import ObjectId
from db import get_database
from middleware import get_current_user
from middleware.auth_middleware import require_paid_user
from services.gemini_service import gemini_service
from services.storage_service import storage_service
from models.leaderboard import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(data: ChatRequest, current_user: dict = Depends(require_paid_user)):
    """Send message to Cannon AI"""
    from services.schedule_service import schedule_service
    db = get_database()
    user_id = current_user["id"]
    
    # Get chat history
    history_doc = await db.chat_history.find_one({"user_id": user_id})
    history = history_doc.get("messages", []) if history_doc else []
    
    # Get active schedule for context
    active_schedule = await schedule_service.get_current_schedule(user_id)
    
    # Get user context
    latest_scan = await db.scans.find_one({"user_id": user_id}, sort=[("created_at", -1)])
    user_context = {
        "latest_scan": latest_scan.get("analysis") if latest_scan else None,
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
                        feedback=feedback
                    )
                    # We could optionally add a notice to the response or refresh the context
            except Exception as e:
                print(f"Chat-triggered schedule adaptation failed: {e}")
    
    # Save to history
    new_messages = history + [
        {
            "role": "user", 
            "content": data.message, 
            "attachment_url": data.attachment_url,
            "attachment_type": data.attachment_type,
            "created_at": datetime.utcnow()
        },
        {"role": "assistant", "content": response_text, "created_at": datetime.utcnow()}
    ]
    
    if history_doc:
        await db.chat_history.update_one({"_id": history_doc["_id"]}, {"$set": {"messages": new_messages[-50:], "updated_at": datetime.utcnow()}})
    else:
        await db.chat_history.insert_one({"user_id": user_id, "messages": new_messages, "created_at": datetime.utcnow()})
    
    return ChatResponse(response=response_text)


@router.get("/history")
async def get_chat_history(limit: int = 50, current_user: dict = Depends(require_paid_user)):
    """Get chat history"""
    db = get_database()
    history_doc = await db.chat_history.find_one({"user_id": current_user["id"]})
    messages = history_doc.get("messages", [])[-limit:] if history_doc else []
    return {"messages": messages}
