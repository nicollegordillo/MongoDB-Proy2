import os
from fastapi import FastAPI, HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from fastapi.responses import StreamingResponse
from pymongo import MongoClient
from bson import ObjectId

# Conexión a MongoDB
mongo_uri = os.environ.get("MONGODB_URI")
if mongo_uri:
    print("Mongo URI cargada exitosamente")
    client = MongoClient(mongo_uri)
    db = client["restaurante_db"]

    # Inicializar FastAPI
    app = FastAPI()

    # ------------------------------
    # RUTA PRINCIPAL
    # ------------------------------

    @app.get("/")
    async def hello():
        return {"mensaje": "Hola desde FastAPI + MongoDB + Vercel"}
else:
    print("Error: MONGODB_URI no configurada.")


# ------------------------------
# CRUD ÓRDENES
# ------------------------------

@app.post("/ordenes/")
async def crear_orden(orden: dict):
    res = await db.ordenes.insert_one(orden)
    return {"id": str(res.inserted_id)}

@app.get("/ordenes/")
async def listar_ordenes(skip: int = 0, limit: int = 10):
    ordenes = await db.ordenes.find().skip(skip).limit(limit).to_list(100)
    for o in ordenes:
        o["_id"] = str(o["_id"])
    return ordenes

@app.get("/ordenes/{id}")
async def obtener_orden(id: str):
    orden = await db.ordenes.find_one({"_id": ObjectId(id)})
    if not orden:
        raise HTTPException(status_code=404)
    orden["_id"] = str(orden["_id"])
    return orden

@app.put("/ordenes/{id}")
async def actualizar_estado(id: str, estado: str):
    res = await db.ordenes.update_one({"_id": ObjectId(id)}, {"$set": {"estado": estado}})
    return {"modificados": res.modified_count}

@app.delete("/ordenes/{id}")
async def eliminar_orden(id: str):
    res = await db.ordenes.delete_one({"_id": ObjectId(id)})
    return {"eliminados": res.deleted_count}

# ------------------------------
# CRUD RESEÑAS
# ------------------------------

@app.post("/resenias/")
async def crear_resenia(resenia: dict):
    res = await db.resenias.insert_one(resenia)
    return {"id": str(res.inserted_id)}

@app.get("/resenias/")
async def listar_resenias():
    resenias = await db.resenias.find().to_list(100)
    for r in resenias:
        r["_id"] = str(r["_id"])
    return resenias

@app.get("/resenias/{id}")
async def obtener_resenia(id: str):
    r = await db.resenias.find_one({"_id": ObjectId(id)})
    if not r:
        raise HTTPException(404)
    r["_id"] = str(r["_id"])
    return r

@app.put("/resenias/{id}")
async def actualizar_resenia(id: str, data: dict):
    res = await db.resenias.update_one({"_id": ObjectId(id)}, {"$set": data})
    return {"modificados": res.modified_count}

@app.delete("/resenias/{id}")
async def eliminar_resenia(id: str):
    res = await db.resenias.delete_one({"_id": ObjectId(id)})
    return {"eliminados": res.deleted_count}

# ------------------------------
# IMÁGENES CON GRIDFS
# ------------------------------

@app.post("/imagenes/")
async def subir_imagen(file: UploadFile):
    fs = AsyncIOMotorGridFSBucket(db)
    contenido = await file.read()
    file_id = await fs.upload_from_stream(file.filename, contenido)
    return {"id": str(file_id)}

@app.get("/imagenes/{id}")
async def obtener_imagen(id: str):
    fs = AsyncIOMotorGridFSBucket(db)
    stream = await fs.open_download_stream(ObjectId(id))
    return StreamingResponse(stream, media_type="image/jpeg")





