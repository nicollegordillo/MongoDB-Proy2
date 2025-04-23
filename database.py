# database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient

client = None

def get_db():
    return client["restaurante_db"]

async def startup_db():
    global client
    MONGO_URI = os.environ.get("MONGODB_URI")
    client = AsyncIOMotorClient(MONGO_URI)
    print("Conectado a MongoDB")

async def shutdown_db():
    global client
    client.close()
    print("Desconectado de MongoDB")

