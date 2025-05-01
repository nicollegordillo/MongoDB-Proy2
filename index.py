import os
from fastapi import FastAPI, HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from fastapi.responses import StreamingResponse
from bson import ObjectId
from contextlib import asynccontextmanager

from models.usuario import Usuario

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

def get_db():
    mongo_uri = os.environ["MONGODB_URI"]
    client = AsyncIOMotorClient(mongo_uri)
    return client["restaurante_db"]

# ------------------------------
# CRUD ÓRDENES
# ------------------------------

@app.post("/ordenes/")
async def crear_orden(orden: dict):
    try:
        db = get_db()
        res = await db.ordenes.insert_one(orden)
        return {"id": str(res.inserted_id)}
    except Exception as e:
        print(f"Error al crear orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ordenes/")
async def listar_ordenes(skip: int = 0, limit: int = 10):
    try:
        db = get_db()
        ordenes_cursor = db.ordenes.find().skip(skip).limit(limit)
        ordenes = await ordenes_cursor.to_list(length=100)
        for o in ordenes:
            o["_id"] = str(o["_id"])
            o["usuario_id"] = str(o["usuario_id"])
            o["restaurante_id"] = str(o["restaurante_id"])
            if o.get("resenia_id"):
                    o["resenia_id"] = str(o["resenia_id"])
            for item in o.get("items", []):
                if item.get("articulo_id"):
                    item["articulo_id"] = str(item["articulo_id"])
        return ordenes
    except Exception as e:
        print(f"Error al listar órdenes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ordenes/{id}")
async def obtener_orden(id: str):
    try:
        db = get_db()
        orden = await db.ordenes.find_one({"_id": ObjectId(id)})
        if not orden:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        orden["_id"] = str(orden["_id"])
        orden["usuario_id"] = str(orden["usuario_id"])
        orden["restaurante_id"] = str(orden["restaurante_id"])
        if orden.get("resenia_id"):
                    orden["resenia_id"] = str(orden["resenia_id"])
        for item in orden.get("items", []):
            if item.get("articulo_id"):
                item["articulo_id"] = str(item["articulo_id"])
        return orden
    except Exception as e:
        print(f"Error al obtener orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/ordenes/{id}")
async def actualizar_estado(id: str, estado: str):
    try:
        db = get_db()
        res = await db.ordenes.update_one({"_id": ObjectId(id)}, {"$set": {"estado": estado}})
        return {"modificados": res.modified_count}
    except Exception as e:
        print(f"Error al actualizar orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/ordenes/{id}")
async def eliminar_orden(id: str):
    try:
        db = get_db()
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
        db = get_db()
        res = await db.resenias.insert_one(resenia)
        return {"id": str(res.inserted_id)}
    except Exception as e:
        print(f"Error al crear reseña: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resenias/")
async def listar_resenias():
    try:
        db = get_db()
        resenias = await db.resenias.find().to_list(100)
        for r in resenias:
            r["_id"] = str(r["_id"])
            r["usuario_id"]= str(r["usuario_id"])
            r["restaurante_id"] = str(r["restaurante_id"])
            r["orden_id"] = str(r["orden_id"])
        return resenias
    except Exception as e:
        print(f"Error al listar reseñas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resenias/{id}")
async def obtener_resenia(id: str):
    try:
        db = get_db()
        r = await db.resenias.find_one({"_id": ObjectId(id)})
        if not r:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")
        r["_id"] = str(r["_id"])
        r["usuario_id"]= str(r["usuario_id"])
        r["restaurante_id"] = str(r["restaurante_id"])
        r["orden_id"] = str(r["orden_id"])
        return r
    except Exception as e:
        print(f"Error al obtener reseña: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/resenias/{id}")
async def actualizar_resenia(id: str, data: dict):
    try:
        db = get_db()
        res = await db.resenias.update_one({"_id": ObjectId(id)}, {"$set": data})
        return {"modificados": res.modified_count}
    except Exception as e:
        print(f"Error al actualizar reseña: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/resenias/{id}")
async def eliminar_resenia(id: str):
    try:
        db = get_db()
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
        db = get_db()
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
        db = get_db()
        fs = AsyncIOMotorGridFSBucket(db)
        stream = await fs.open_download_stream(ObjectId(id))
        return StreamingResponse(stream, media_type="image/jpeg")
    except Exception as e:
        print(f"Error al obtener imagen: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

# ------------------------------
# CRUD RESTAURANTES
# ------------------------------
 
@app.get("/restaurantes/")
async def listar_restaurantes():
    try:
        db = get_db()
        restaurantes = await db.restaurantes.find().to_list(100)
        for r in restaurantes:
            r["_id"] = str(r["_id"])
        return restaurantes
    except Exception as e:
        print(f"Error al obtener restaurantes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/restaurantes/{id}")
async def obtener_restaurante(id: str):
    try:
        db = get_db()
        r = await db.restaurantes.find_one({"_id": ObjectId(id)})
        if not r:
            raise HTTPException(status_code=404, detail="Restaurante no encontrada")
        r["_id"] = str(r["_id"])
        return r
    except Exception as e:
        print(f"Error al obtener restaurante: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/restaurantes/")
async def crear_restaurante(rest: dict):
    try:
        db = get_db()
        res = await db.restaurantes.insert_one(rest)
        return {"id": str(res.inserted_id)}
    except Exception as e:
        print(f"Error al crear reseña: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/restaurantes/{id}")
async def eliminar_restaurante():
    try:
        db = get_db()
        r = await db.restaurantes.delete_one({"_id": ObjectId(id)})
        return {"eliminados": r.deleted_count}
    except Exception as e:
        print(f"Error al eliminar restaurante: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/restaurantes/{id}")
async def actualizar_restaurante(id: str, data: dict):
    try:
        db = get_db()
        res = await db.restaurante.update_one({"_id": ObjectId(id)}, {"$set": data})
        return {"modificados": res.modified_count}
    except Exception as e:
        print(f"Error al actualizar restaurante: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# ------------------------------
# AGREGATION
# ------------------------------

# Top restaurantes (mejor calificacion)
@app.post("/agg/top-res/{limit}")
async def top_restaurantes(limit: int):
    try:
        db = get_db()
        cursor = db.restaurantes.aggregate([
            {"$sort": {"calificacionPromedio": -1}},
            {"$limit": limit}
        ])
        res = await cursor.to_list(length=limit) 
        return res
    except Exception as e:
        print(f"Error obteniendo top restaurantes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# Top articulos (mas vendidos)
@app.post("/agg/top-dish/{limit}")
async def top_platos(limit: int):
    try:
        db = get_db()
        cursor = db.ordenes.aggregate([
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.articulo_id",
                "total_sales": {"$sum": "$items.cantidad"}
            }},
            {"$sort": {"total_sales": -1}},
            {"$limit": limit},
            {"$project": {
                "_id": 0,
                "articulo_id": "$_id",
                "total_sales": 1
            }},
            {"$lookup": {
                "from": "articulos",
                "let": {
                    "articulo_id": "$articulo_id"
                },
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$eq": ["$_id", "$$articulo_id"]
                        }
                    }}
                ],
                "as": "articulo"
            }},
            {"$project": {
                "total_sales": 1,
                "articulo": 1
            }}
        ])
        res = await cursor.to_list(length=limit) 
        return res
    except Exception as e:
        print(f"Error alobteniendo top restaurante: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Gastos de clientes (gasto total por cada cliente)
@app.post("/agg/user-spent/")
async def gastos_usuario():
    try:
        db = get_db()
        cursor = db.ordenes.aggregate([
            {"$group": {
                "_id": "$usuario_id",
                "spent": {"$sum": "$total"}
            }}
        ])
        res = await cursor.to_list() 
        return res
    except Exception as e:
        print(f"Error alobteniendo top restaurante: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agg/resenias/{id}")
async def resenias_por_restaurante(id: str):
    try:
        db = get_db()
        cursor = db.resenias.aggregate([
            {"$match": { 
                "restaurante_id": ObjectId(id) 
            }},
            # Info de usuario
            {"$lookup": {
                "from": "usuarios",
                "let": {
                    "usuario_id": "$usuario_id"
                },
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$eq": ["$_id", "$$usuario_id"]
                        }
                    }},
                    {"$project": {
                        "nombre": "$nombre",
                        "correo": "$correo"
                    }}
                ],
                "as": "user_info"
            }},
            # Info de orden
            {"$lookup": {
                "from": "ordenes",
                "let": {
                    "orden_id": "$orden_id"
                },
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$eq": ["$_id", "$$orden_id"]
                        }
                    }},
                    {"$project": {
                        "estado": "$estado",
                        "total": "$total",
                        "items": "$items"
                    }}
                ],
                "as": "order_info"
            }},
            # integracion
            {"$project": {
                "user_info": "$user_info",
                "order_info": "$order_info",
                "comentario": "$comentario",
                "calificacion": "&calificacion",
                "fecha": "$fecha"
            }}
        ])
        res = await cursor.to_list() 
        return res
    except Exception as e:
        print(f"Error obteniendo top restaurantes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# ------------------------------
# CRUD USUARIOS
# ------------------------------

@app.post("/usuarios/")
async def crear_usuario(usuario: Usuario):
    try:
        db = get_db()
        res = await db.usuarios.insert_one(usuario.dict())
        return {"id": str(res.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/usuarios/")
async def listar_usuarios(tipo: str = None, correo: str = None, nombre: str = None):
    try:
        db = get_db()
        filtro = {}
        if tipo: filtro["tipo"] = tipo
        if correo: filtro["correo"] = correo
        if nombre: filtro["nombre"] = {"$regex": nombre, "$options": "i"}
        usuarios = await db.usuarios.find(filtro).to_list(100)
        for u in usuarios: u["_id"] = str(u["_id"])
        return usuarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usuarios/{id}")
async def obtener_usuario(id: str):
    try:
        db = get_db()
        u = await db.usuarios.find_one({"_id": ObjectId(id)})
        if not u: raise HTTPException(status_code=404, detail="Usuario no encontrado")
        u["_id"] = str(u["_id"])
        return u
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.put("/usuarios/{id}")
async def actualizar_usuario(id: str, data: dict):
    try:
        db = get_db()
        res = await db.usuarios.update_one({"_id": ObjectId(id)}, {"$set": data})
        return {"modificados": res.modified_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/usuarios/{id}")
async def eliminar_usuario(id: str):
    try:
        db = get_db()
        res = await db.usuarios.delete_one({"_id": ObjectId(id)})
        return {"eliminados": res.deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


