import os
from motor.motor_asyncio import AsyncIOMotorClient

async def create_db():
    MONGO_URI = os.environ.get("MONGODB_URI")
    client = AsyncIOMotorClient(MONGO_URI)
    return client["restaurante_db"]



