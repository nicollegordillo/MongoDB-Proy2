from fastapi import APIRouter, UploadFile
from index import db
import gridfs
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

router = APIRouter()
fs = AsyncIOMotorGridFSBucket(db)

@router.post("/")
async def subir_imagen(file: UploadFile):
    contenido = await file.read()
    file_id = await fs.upload_from_stream(file.filename, contenido)
    return {"id": str(file_id)}

@router.get("/{id}")
async def obtener_imagen(id: str):
    from fastapi.responses import StreamingResponse
    stream = await fs.open_download_stream(ObjectId(id))
    return StreamingResponse(stream, media_type="image/jpeg")
