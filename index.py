import os
from fastapi import FastAPI, HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from fastapi.responses import StreamingResponse
from bson import ObjectId
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear índices al iniciar
    try:
        print(" Creando índices...")

        # Índices para órdenes
        await db.ordenes.create_index([("fecha", -1)])
        await db.ordenes.create_index([("usuario_id", 1), ("fecha", -1)])
        await db.ordenes.create_index([("estado", 1)])
        await db.ordenes.create_index([("items.articulo_id", 1)])  # multikey

        # Índices para reseñas
        await db.resenias.create_index([("fecha", -1)])
        await db.resenias.create_index([("restaurante_id", 1), ("calificacion", -1)])
        await db.resenias.create_index([("usuario_id", 1)])

        # Indices para restaurantes
        await db.restaurantes.create_index([("direccion.coordenadas","2dsphere")])
        await db.restaurantes.create_index([("nombre",-1)])
        await db.restaurantes.create_index([("categorias",1)])
        await db.restaurantes.create_index([("calificacionPromedio",-1)])
        
        print(" Índices creados correctamente.")
    except Exception as e:
        print(f" Error creando índices: {e}")

    yield  # Aquí continúa la ejecución normal de la app


# Conexión a MongoDB
mongo_uri = os.environ.get("MONGODB_URI")
if mongo_uri:
    print("Mongo URI cargada exitosamente")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["restaurante_db"]
    
    # Inicializar FastAPI
    app = FastAPI(lifespan=lifespan)

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
    try:
        res = await db.ordenes.insert_one(orden)
        return {"id": str(res.inserted_id)}
    except Exception as e:
        print(f"Error al crear orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ordenes/")
async def listar_ordenes(skip: int = 0, limit: int = 10):
    try:
        ordenes = await db.ordenes.find().skip(skip).limit(limit).to_list(100)
        for o in ordenes:
            o["_id"] = str(o["_id"])
        return ordenes
    except Exception as e:
        print(f"Error al listar órdenes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ordenes/{id}")
async def obtener_orden(id: str):
    try:
        orden = await db.ordenes.find_one({"_id": ObjectId(id)})
        if not orden:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        orden["_id"] = str(orden["_id"])
        return orden
    except Exception as e:
        print(f"Error al obtener orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/ordenes/{id}")
async def actualizar_estado(id: str, estado: str):
    try:
        res = await db.ordenes.update_one({"_id": ObjectId(id)}, {"$set": {"estado": estado}})
        return {"modificados": res.modified_count}
    except Exception as e:
        print(f"Error al actualizar orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/ordenes/{id}")
async def eliminar_orden(id: str):
    try:
        res = await db.ordenes.delete_one({"_id": ObjectId(id)})
        return {"eliminados": res.deleted_count}
    except Exception as e:
        print(f"Error al eliminar orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------
# CRUD RESEÑAS
# ------------------------------

@app.post("/resenias/")
async def crear_resenia(resenia: dict):
    try:
        res = await db.resenias.insert_one(resenia)
        return {"id": str(res.inserted_id)}
    except Exception as e:
        print(f"Error al crear reseña: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resenias/")
async def listar_resenias():
    try:
        resenias = await db.resenias.find().to_list(100)
        for r in resenias:
            r["_id"] = str(r["_id"])
        return resenias
    except Exception as e:
        print(f"Error al listar reseñas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resenias/{id}")
async def obtener_resenia(id: str):
    try:
        r = await db.resenias.find_one({"_id": ObjectId(id)})
        if not r:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")
        r["_id"] = str(r["_id"])
        return r
    except Exception as e:
        print(f"Error al obtener reseña: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/resenias/{id}")
async def actualizar_resenia(id: str, data: dict):
    try:
        res = await db.resenias.update_one({"_id": ObjectId(id)}, {"$set": data})
        return {"modificados": res.modified_count}
    except Exception as e:
        print(f"Error al actualizar reseña: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/resenias/{id}")
async def eliminar_resenia(id: str):
    try:
        res = await db.resenias.delete_one({"_id": ObjectId(id)})
        return {"eliminados": res.deleted_count}
    except Exception as e:
        print(f"Error al eliminar reseña: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------
# IMÁGENES CON GRIDFS
# ------------------------------

@app.post("/imagenes/")
async def subir_imagen(file: UploadFile):
    try:
        fs = AsyncIOMotorGridFSBucket(db)
        contenido = await file.read()
        file_id = await fs.upload_from_stream(file.filename, contenido)
        return {"id": str(file_id)}
    except Exception as e:
        print(f"Error al subir imagen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/imagenes/{id}")
async def obtener_imagen(id: str):
    try:
        fs = AsyncIOMotorGridFSBucket(db)
        stream = await fs.open_download_stream(ObjectId(id))
        return StreamingResponse(stream, media_type="image/jpeg")
    except Exception as e:
        print(f"Error al obtener imagen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------
# CRUD RESTAURANTES
# ------------------------------

@app.post("/restaurantes/")
async def crear_restaurante(rest: dict):
    try:
        res = await db.restaurantes.insert_one(rest)
        return {"id": str(res.inserted_id)}
    except Exception as e:
        print(f"Error al crear reseña: {e}")
        raise HTTPException(status_code=500, detail=str(e))

app.get("/restaurantes/{id}")
async def obtener_restaurante(id: str):
    try:
        r = await db.restaurantes.find_one({"_id": ObjectId(id)})
        if not r:
            raise HTTPException(status_code=404, detail="Restaurante no encontrada")
        r["_id"] = str(r["_id"])
        return r
    except Exception as e:
        print(f"Error al obtener restaurante: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
app.get("/restaurantes")
async def obtener_restaurante():
    try:
        r = await db.restaurantes.find().to_list(100)
        if not r:
            raise HTTPException(status_code=404, detail="Restaurante no encontrada")
        r["_id"] = str(r["_id"])
        return r
    except Exception as e:
        print(f"Error al obtener restaurantes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

app.delete("/restaurantes/{id}")
async def eliminar_restaurante():
    try:
        r = await db.restaurantes.delete_one({"_id": ObjectId(id)})
        return {"eliminados": r.deleted_count}
    except Exception as e:
        print(f"Error al eliminar restaurante: {e}")
        raise HTTPException(status_code=500, detail=str(e))

app.put("/restaurantes/{id}")
async def actualizar_restaurante(id: str, data: dict):
    try:
        res = await db.actualizar_restaurante.update_one({"_id": ObjectId(id)}, {"$set": data})
        return {"modificados": res.modified_count}
    except Exception as e:
        print(f"Error al actualizar restaurante: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# ------------------------------
# AGREGATION
# ------------------------------

app.post("/agg/top/{limit}")
async def obtener_restaurante(limit: int):
    try:
        res = await db.resenias.aggregate([
            {"$sort": {"calificacionPromedio": -1}},
            {"$limit": limit}
        ])
        return res
    except Exception as e:
        print(f"Error alobteniendo top restaurante: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    