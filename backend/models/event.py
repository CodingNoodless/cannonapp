"""
Event Models - TikTok Live events
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


class EventCreate(BaseModel):
    """Request to create a new event (admin)"""
    title: str
    description: str
    tiktok_link: str
    scheduled_at: datetime
    thumbnail_url: Optional[str] = None
    duration_minutes: int = Field(default=60, ge=1)


class EventResponse(BaseModel):
    """Event response for API"""
    id: str
    title: str
    description: str
    tiktok_link: str
    scheduled_at: datetime
    thumbnail_url: Optional[str] = None
    duration_minutes: int
    is_live: bool = False
    is_past: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class EventInDB(BaseModel):
    """Full event model as stored in database"""
    title: str
    description: str
    tiktok_link: str
    scheduled_at: datetime
    thumbnail_url: Optional[str] = None
    duration_minutes: int = 60
    is_live: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CalendarEvent(BaseModel):
    """Event for calendar view"""
    id: str
    title: str
    scheduled_at: datetime
    duration_minutes: int
    is_live: bool
