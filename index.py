# index.py
import os
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

from routes.ordenes import router as ordenes_router
from routes.resenias import router as resenias_router
from routes.imagenes import router as imagenes_router

mongo_uri = os.environ.get("MONGODB_URI")
client = AsyncIOMotorClient(mongo_uri)
db = client["restaurante_db"]

app = FastAPI()

app.include_router(ordenes_router, prefix="/ordenes", tags=["Ordenes"])
app.include_router(resenias_router, prefix="/resenias", tags=["Resenias"])
app.include_router(imagenes_router, prefix="/imagenes", tags=["Imagenes"])

@app.get("/")
async def hello():
    return {"mensaje": "Hola desde FastAPI + MongoDB + Vercel"}





