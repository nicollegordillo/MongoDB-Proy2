import os
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    MONGO_URI = os.environ.get("MONGODB_URI")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client["restaurante_db"]
    app.state.db = db  #  aquí se agrega correctamente al estado
    yield
    client.close()  # Cierre opcional


