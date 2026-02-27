import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DATABASE", "cannon_db")

async def fix_announcements_channel():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    print(f"Connecting to {MONGODB_URI}, DB: {DB_NAME}")
    
    # Update announcements channel to be is_admin_only
    result = await db.forums.update_one(
        {"slug": "announcements"},
        {"$set": {"is_admin_only": True}}
    )
    
    if result.matched_count > 0:
        print(f"Successfully updated #announcements channel. Modified: {result.modified_count}")
    else:
        print("Announcements channel with slug 'announcements' not found!")
    
    # Verify current state
    channel = await db.forums.find_one({"slug": "announcements"})
    if channel:
        print(f"Current state of #announcements: is_admin_only = {channel.get('is_admin_only')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_announcements_channel())
