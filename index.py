from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes.ordenes import router as ordenes_router
from routes.resenias import router as resenias_router
from routes.imagenes import router as imagenes_router
from database import create_db

# Definimos la función lifespan primero
@asynccontextmanager
async def lifespan(app: FastAPI):
    db = await create_db()  # Inicializamos la base de datos
    app.state.db = db  # Asignamos db al estado de la app
    yield  # El ciclo de vida continúa durante la app
    db.client.close()  # Cerramos la conexión cuando la app se apague

# Ahora instanciamos la app y le pasamos lifespan
app = FastAPI(lifespan=lifespan)

# Montamos los routers
app.include_router(ordenes_router, prefix="/ordenes", tags=["Ordenes"])
app.include_router(resenias_router, prefix="/resenias", tags=["Resenias"])
app.include_router(imagenes_router, prefix="/imagenes", tags=["Imagenes"])

@app.get("/")
async def hello():
    return {"mensaje": "Hola desde FastAPI + MongoDB + Vercel"}




