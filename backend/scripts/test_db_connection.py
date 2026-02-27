import asyncio
import sys
import os

# Add the current directory to sys.path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.mongo import mongo_client
from config import settings

async def test_connection():
    print(f"Attempting to connect to: {settings.mongodb_database}")
    try:
        await mongo_client.connect()
        db = mongo_client.get_database()
        
        # Try a simple ping
        await db.command("ping")
        print("✅ Ping successful!")
        
        # List collections
        collections = await db.list_collection_names()
        print(f"✅ Collections found: {collections}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await mongo_client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_connection())
