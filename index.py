from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes.ordenes import router as ordenes_router
from routes.resenias import router as resenias_router
from routes.imagenes import router as imagenes_router
from database import create_db

db = None  # para compartirlo entre rutas

@asynccontextmanager
async def lifespan(app: FastAPI):
    from database import create_db
    db = await create_db()
    app.state.db = db  # Lo asignas aquí, no como variable global
    yield
    # Puedes cerrar conexión si lo necesitas, ej. `await db.client.close()`

app = FastAPI(lifespan=lifespan)

# Montar routers
app.include_router(ordenes_router, prefix="/ordenes", tags=["Ordenes"])
app.include_router(resenias_router, prefix="/resenias", tags=["Resenias"])
app.include_router(imagenes_router, prefix="/imagenes", tags=["Imagenes"])

@app.get("/")
async def hello():
    return {"mensaje": "Hola desde FastAPI + MongoDB + Vercel"}



