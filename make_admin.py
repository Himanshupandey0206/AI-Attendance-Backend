import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def main():
    print("Connecting to DB...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    result = await db.users.update_many({}, {"$set": {"role": "admin"}})
    print(f"Successfully upgraded {result.modified_count} users to 'admin' role!")

if __name__ == "__main__":
    asyncio.run(main())
