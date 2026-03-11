"""
Users API - Profile and Onboarding
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from datetime import datetime
from bson import ObjectId
from typing import List, Optional

from db import get_database
from middleware import get_current_user
from services.storage_service import storage_service
from models.user import (
    UserResponse, OnboardingData, UserProfile, GoalType, ExperienceLevel, AccountUpdateRequest
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user's profile
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        first_name=current_user.get("first_name"),
        last_name=current_user.get("last_name"),
        username=current_user.get("username"),
        created_at=current_user["created_at"],
        is_paid=current_user.get("is_paid", False),
        subscription_status=current_user.get("subscription_status"),
        subscription_end_date=current_user.get("subscription_end_date"),
        onboarding=OnboardingData(**current_user.get("onboarding", {})),
        profile=UserProfile(**current_user.get("profile", {})),
        first_scan_completed=current_user.get("first_scan_completed", False),
        is_admin=current_user.get("is_admin", False)
    )


@router.post("/onboarding")
async def save_onboarding(
    data: OnboardingData,
    current_user: dict = Depends(get_current_user)
):
    """
    Save onboarding questionnaire answers
    """
    db = get_database()
    
    # Update onboarding data
    onboarding_data = data.model_dump()
    onboarding_data["completed"] = True
    
    await db.users.update_one(
        {"_id": ObjectId(current_user["id"])},
        {
            "$set": {
                "onboarding": onboarding_data,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Onboarding completed", "data": onboarding_data}


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload profile picture
    """
    db = get_database()
    
    # Read file content
    content = await file.read()
    
    # Upload to storage
    avatar_url = await storage_service.upload_image(
        content,
        current_user["id"],
        image_type="avatar"
    )
    
    if not avatar_url:
        raise HTTPException(status_code=500, detail="Failed to upload image")
    
    # Update user profile
    await db.users.update_one(
        {"_id": ObjectId(current_user["id"])},
        {
            "$set": {
                "profile.avatar_url": avatar_url,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"avatar_url": avatar_url}


@router.put("/profile")
async def update_profile(
    profile: UserProfile,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user profile
    """
    db = get_database()
    
    # Merge with existing profile data to avoid overwriting unrelated fields
    current_profile = current_user.get("profile", {})
    updated_data = profile.model_dump(exclude_unset=True)
    
    # Combine (pydantic model dump might miss existing fields if not careful)
    # Actually, we can just use dot notation for specific fields or merge dicts
    # But since UserProfile replaces the whole object structure in pydantic, 
    # we should likely merge.
    # Simple approach: Update provided fields.
    
    # Construct update dict using dot notation for safety
    update_fields = {}
    for key, value in updated_data.items():
        update_fields[f"profile.{key}"] = value
        
    update_fields["updated_at"] = datetime.utcnow()

    await db.users.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": update_fields}
    )
    
    return {"message": "Profile updated"}


@router.put("/account")
async def update_account(
    data: AccountUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user account info (first_name, last_name, username)
    Note: Email cannot be changed
    """
    db = get_database()
    
    update_fields = {}
    
    if data.first_name is not None:
        update_fields["first_name"] = data.first_name.strip() if data.first_name.strip() else None
    if data.last_name is not None:
        update_fields["last_name"] = data.last_name.strip() if data.last_name.strip() else None
    if data.username is not None:
        username_clean = data.username.strip()
        if username_clean:
            # Validate username format
            if len(username_clean) < 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username must be at least 3 characters"
                )
            if not username_clean.replace('_', '').isalnum():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username can only contain letters, numbers, and underscores"
                )
            # Check if username is already taken by another user
            existing = await db.users.find_one({
                "username": username_clean.lower(),
                "_id": {"$ne": ObjectId(current_user["id"])}
            })
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            update_fields["username"] = username_clean.lower()
        else:
            update_fields["username"] = None
    
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    update_fields["updated_at"] = datetime.utcnow()
    
    await db.users.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": update_fields}
    )
    
    return {"message": "Account updated"}


@router.get("/goals", response_model=List[str])
async def get_available_goals():
    """
    Get list of available improvement goals
    """
    return [goal.value for goal in GoalType]


@router.get("/experience-levels", response_model=List[str])
async def get_experience_levels():
    """
    Get list of experience levels
    """
    return [level.value for level in ExperienceLevel]
