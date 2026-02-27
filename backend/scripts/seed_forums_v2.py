import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DATABASE", "cannon_db")

async def seed_forums_v2():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    print(f"Connecting to {MONGODB_URI}, DB: {DB_NAME}")
    
    # 1. Clear announcements messages
    announcement_channel = await db.forums.find_one({"slug": "announcements"})
    if announcement_channel:
        a_id = str(announcement_channel["_id"])
        res = await db.channel_messages.delete_many({"channel_id": a_id})
        print(f"Cleared {res.deleted_count} messages from #announcements.")
    else:
        # Create announcements if it doesn't exist
        print("Announcements channel not found, creating it...")
        await db.forums.insert_one({
            "name": "Announcements",
            "slug": "announcements",
            "description": "Official updates from the Goliath team.",
            "is_admin_only": True,
            "order": 0,
            "created_at": datetime.utcnow()
        })

    # 2. Add more relevant channels
    extra_channels = [
        {
            "name": "General Discussion",
            "slug": "general",
            "description": "Talk about anything looksmaxxing and self-improvement.",
            "is_admin_only": False,
            "order": 1
        },
        {
            "name": "Mewing Hacks",
            "slug": "mewing-hacks",
            "description": "Share your mewing routines and results.",
            "is_admin_only": False,
            "order": 2
        },
        {
            "name": "Shredding & Fitness",
            "slug": "fitness",
            "description": "Nutrition, gym routines, and getting lean.",
            "is_admin_only": False,
            "order": 3
        },
        {
            "name": "Skincare & Grooming",
            "slug": "skincare",
            "description": "Best products and routines for clear skin.",
            "is_admin_only": False,
            "order": 4
        },
        {
            "name": "Style & Fashion",
            "slug": "style",
            "description": "Clothing, haircuts, and aesthetic advice.",
            "is_admin_only": False,
            "order": 5
        },
        {
            "name": "Mindset Mastery",
            "slug": "mindset",
            "description": "Mental health, confidence, and discipline.",
            "is_admin_only": False,
            "order": 6
        },
        {
            "name": "Nutrition & Diet",
            "slug": "nutrition",
            "description": "Eating for your goals.",
            "is_admin_only": False,
            "order": 7
        }
    ]

    for ch in extra_channels:
        # Avoid duplicates
        existing = await db.forums.find_one({"slug": ch["slug"]})
        if not existing:
            ch["created_at"] = datetime.utcnow()
            await db.forums.insert_one(ch)
            print(f"Added channel: #{ch['slug']}")
        else:
            print(f"Channel #{ch['slug']} already exists, skipping.")

    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_forums_v2())
