from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes.ordenes import router as ordenes_router
from routes.resenias import router as resenias_router
from routes.imagenes import router as imagenes_router
from database import create_db



async def create_lifespan():
    db = await create_db()  # Inicializar la base de datos
    try:
        yield db  # El db estará disponible durante el ciclo de vida de la app
    finally:
        db.client.close()  # Cerrar la conexión al finalizar la app

app = FastAPI(lifespan=create_lifespan())

# Montar routers
app.include_router(ordenes_router, prefix="/ordenes", tags=["Ordenes"])
app.include_router(resenias_router, prefix="/resenias", tags=["Resenias"])
app.include_router(imagenes_router, prefix="/imagenes", tags=["Imagenes"])

@app.get("/")
async def hello():
    return {"mensaje": "Hola desde FastAPI + MongoDB + Vercel"}




