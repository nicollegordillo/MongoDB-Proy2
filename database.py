import os
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

@asynccontextmanager
async def create_db():
    MONGO_URI = os.environ.get("MONGODB_URI")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client["restaurante_db"]
    try:
        yield db  # Aseguramos que db esté disponible durante el ciclo de vida de la app
    finally:
        client.close()  # Cerramos la conexión cuando la app termine



