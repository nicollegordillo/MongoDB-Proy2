from fastapi import APIRouter, UploadFile, Request
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.post("/")
async def subir_imagen(request: Request, file: UploadFile):
    db = request.app.state.db
    fs = AsyncIOMotorGridFSBucket(db)
    contenido = await file.read()
    file_id = await fs.upload_from_stream(file.filename, contenido)
    return {"id": str(file_id)}

@router.get("/{id}")
async def obtener_imagen(request: Request, id: str):
    db = request.app.state.db
    fs = AsyncIOMotorGridFSBucket(db)
    stream = await fs.open_download_stream(ObjectId(id))
    return StreamingResponse(stream, media_type="image/jpeg")

