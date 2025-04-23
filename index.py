from fastapi import FastAPI
from routes.ordenes import router as ordenes_router
from routes.resenias import router as resenias_router
from routes.imagenes import router as imagenes_router
from mangum import Mangum
from dotenv import load_dotenv
from fastapi.responses import FileResponse
import os

load_dotenv()

app = FastAPI()

app.include_router(ordenes_router, prefix="/ordenes", tags=["Ordenes"])
app.include_router(resenias_router, prefix="/resenias", tags=["Resenias"])
app.include_router(imagenes_router, prefix="/imagenes", tags=["Imagenes"])

@app.get("/")
async def hello():
    return {"mensaje": "Hola desde FastAPI + MongoDB + Vercel"}

handler = Mangum(app)

@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join("static", "favicon.ico"))

