import os
from fastapi import Body, FastAPI, HTTPException, UploadFile, Query
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from fastapi.responses import StreamingResponse
from bson import ObjectId
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime

from pymongo import InsertOne, UpdateOne

from models.articulo import Articulo
from models.usuario import Usuario
from models.restaurantes import RestauranteOptions, Restaurante

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
async def crear_orden(orden_dict: dict):
    try:
        db = get_db()
        orden_dict["usuario_id"] = ObjectId(orden_dict["usuario_id"])
        orden_dict["restaurante_id"] = ObjectId(orden_dict["restaurante_id"])
        if orden_dict["resenia_id"]:
            orden_dict["resenia_id"] = ObjectId(orden_dict["resenia_id"])

        # Convertir IDs de artículos
        for item in orden_dict["items"]:
            item["articulo_id"] = ObjectId(item["articulo_id"])

        res = await db.ordenes.insert_one(orden_dict)
        return {"id": str(res.inserted_id)}
    except Exception as e:
        print(f"Error al crear orden: {e}")
        raise HTTPException(status_code=500, detail="Error al crear la orden")

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

@app.get("/ordenes/filtrar")
async def filtrar_ordenes(
    usuario_id: Optional[str] = None,
    estado: Optional[str] = None,
    fecha: Optional[str] = None,  # formato ISO: "2025-05-01"
    campos: Optional[str] = Query(default=None, description="Ej: usuario_id,estado"),
    ordenar_por: Optional[str] = Query(default=None, description="Ej: fecha,-estado"),
    skip: int = 0,
    limit: int = 10
):
    try:
        db = get_db()
        filtro = {}

        if usuario_id:
            filtro["usuario_id"] = ObjectId(usuario_id)
        if estado:
            filtro["estado"] = estado
        if fecha:
            filtro["fecha"] = {"$regex": f"^{fecha}"}

        # Proyección
        proyeccion = None
        if campos:
            proyeccion = {campo.strip(): 1 for campo in campos.split(",")}
            proyeccion["_id"] = 1  # asegúrate de incluir el _id si se requiere

        # Ordenamiento
        ordenamiento = []
        if ordenar_por:
            for campo in ordenar_por.split(","):
                if campo.startswith("-"):
                    ordenamiento.append((campo[1:], -1))
                else:
                    ordenamiento.append((campo, 1))

        cursor = db.ordenes.find(filtro, proyeccion)
        if ordenamiento:
            cursor = cursor.sort(ordenamiento)
        cursor = cursor.skip(skip).limit(limit)

        ordenes = await cursor.to_list(length=100)
        for o in ordenes:
            o["_id"] = str(o["_id"])
            if "usuario_id" in o: o["usuario_id"] = str(o["usuario_id"])
            if "restaurante_id" in o: o["restaurante_id"] = str(o["restaurante_id"])
            if o.get("resenia_id"): o["resenia_id"] = str(o["resenia_id"])
            for item in o.get("items", []):
                if item.get("articulo_id"): item["articulo_id"] = str(item["articulo_id"])
        return ordenes
    except Exception as e:
        print(f"Error al filtrar órdenes: {e}")
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
    
@app.put("/ordenes/{id}/general")
async def actualizar_orden(id: str, orden_actualizada: dict = Body(...)):
    try:
        db = get_db()
        
        # Conversión opcional de IDs a ObjectId
        if "usuario_id" in orden_actualizada:
            orden_actualizada["usuario_id"] = ObjectId(orden_actualizada["usuario_id"])
        if "restaurante_id" in orden_actualizada:
            orden_actualizada["restaurante_id"] = ObjectId(orden_actualizada["restaurante_id"])
        if "resenia_id" in orden_actualizada and orden_actualizada["resenia_id"]:
            orden_actualizada["resenia_id"] = ObjectId(orden_actualizada["resenia_id"])
        if "items" in orden_actualizada:
            for item in orden_actualizada["items"]:
                if "articulo_id" in item:
                    item["articulo_id"] = ObjectId(item["articulo_id"])

        res = await db.ordenes.update_one({"_id": ObjectId(id)}, {"$set": orden_actualizada})
        return {"modificados": res.modified_count}
    except Exception as e:
        print(f"Error al actualizar orden: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/ordenes/")
async def eliminar_ordenes(ids: List[str] = Body(...)):
    try:
        db = get_db()
        object_ids = [ObjectId(i) for i in ids]
        res = await db.ordenes.delete_many({"_id": {"$in": object_ids}})
        return {"eliminados": res.deleted_count}
    except Exception as e:
        print(f"Error al eliminar órdenes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------
# CRUD RESEÑAS
# ------------------------------

@app.post("/resenias/")
async def crear_resenia(resenia: dict):
    try:
        db = get_db()

        # Validar y convertir IDs a ObjectId
        for campo in ["usuario_id", "restaurante_id", "orden_id"]:
            if campo not in resenia:
                raise HTTPException(status_code=400, detail=f"Falta el campo '{campo}'")
            try:
                resenia[campo] = ObjectId(resenia[campo])
            except Exception:
                raise HTTPException(status_code=400, detail=f"'{campo}' no es un ObjectId válido")

        res = await db.resenias.insert_one(resenia)

        # Actualizar la orden para agregar la reseña 
        await db.ordenes.update_one(
            {"_id": resenia["orden_id"]},
            {"$set": {"resenia_id": res.inserted_id}}
        )

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

@app.get("/resenias/filtrar")
async def filtrar_resenias(
    restaurante_id: Optional[str] = None,
    calificacion: Optional[int] = None,
    campos: Optional[str] = Query(default=None, description="Ej: calificacion,comentario"),
    ordenar_por: Optional[str] = Query(default=None, description="Ej: calificacion,-_id"),
    skip: int = 0,
    limit: int = 10
):
    try:
        db = get_db()
        filtro = {}

        if restaurante_id:
            filtro["restaurante_id"] = ObjectId(restaurante_id)
        if calificacion is not None:
            if calificacion < 1 or calificacion > 5:
                raise HTTPException(status_code=400, detail="calificación debe estar entre 1 y 5")
            filtro["calificacion"] = calificacion

        proyeccion = None
        if campos:
            proyeccion = {campo.strip(): 1 for campo in campos.split(",")}
            proyeccion["_id"] = 1

        ordenamiento = []
        if ordenar_por:
            for campo in ordenar_por.split(","):
                if campo.startswith("-"):
                    ordenamiento.append((campo[1:], -1))
                else:
                    ordenamiento.append((campo, 1))

        cursor = db.resenias.find(filtro, proyeccion)
        if ordenamiento:
            cursor = cursor.sort(ordenamiento)
        cursor = cursor.skip(skip).limit(limit)

        resenias = await cursor.to_list(length=100)
        for r in resenias:
            r["_id"] = str(r["_id"])
            if "usuario_id" in r: r["usuario_id"] = str(r["usuario_id"])
            if "restaurante_id" in r: r["restaurante_id"] = str(r["restaurante_id"])
            if "orden_id" in r: r["orden_id"] = str(r["orden_id"])
        return resenias
    except Exception as e:
        print(f"Error al filtrar reseñas: {e}")
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

        # Convertir IDs si están presentes
        for campo in ["usuario_id", "restaurante_id", "orden_id"]:
            if campo in data:
                try:
                    data[campo] = ObjectId(data[campo])
                except Exception:
                    raise HTTPException(status_code=400, detail=f"'{campo}' no es un ObjectId válido")

        res = await db.resenias.update_one({"_id": ObjectId(id)}, {"$set": data})
        return {"modificados": res.modified_count}
    except Exception as e:
        print(f"Error al actualizar reseña: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/resenias/")
async def eliminar_resenias(ids: List[str] = Body(...)):
    try:
        db = get_db()
        object_ids = [ObjectId(i) for i in ids]
        res = await db.resenias.delete_many({"_id": {"$in": object_ids}})
        return {"eliminados": res.deleted_count}
    except Exception as e:
        print(f"Error al eliminar reseñas: {e}")
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
        
        parsed = convert_object_ids(r)
        return parsed
    except Exception as e:
        print(f"Error al obtener restaurante: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/restaurantes/list")
async def options_restaurante(body: RestauranteOptions = Body(...)):
    try: 
        db = get_db()
        pipeline = []
        # 1. Filtros simples
        if body.simple_filter:
            simple_filter = []
            for key, value in body.simple_filter.items():
                simple_filter.append({
                    "$eq": [ f"${key}",f"{value}" ]
                })
            pipeline.append(
            {"$match": {
                "$expr": {
                    "$and": simple_filter
                }
            }})
        # 2. Categorias
        if body.categories:
            pipeline.append(
            {"$match": {
                "$expr": {
                    "$gt": [
                        {"$size": {
                            "$setIntersection": ["$categorias", body.categories]
                        }},0
                    ]
                }
            }}
            )
        # 3. Sort
        if body.simple_sort:
            simple_sort = {}
            for key, value in body.simple_sort.items():
                simple_sort[key] = value
            pipeline.append({
                "$sort": simple_sort
            })
        # 4. Skip
        if body.skip:
            pipeline.append({"$skip": body.skip})
        if body.limit:
            pipeline.append({"$limit": body.limit})
    
        cursor = db.restaurantes.aggregate(pipeline)
        result = await cursor.to_list()
        parsed = convert_object_ids(result)
        return parsed
    except Exception as e:
        print(f"Error al obtener restaurantes: {e}")
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
async def eliminar_restaurante(id: str):
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
        res = await db.restaurantes.update_one({"_id": ObjectId(id)}, {"$set": data})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Restaurante no encontrado")
    except Exception as e:
        print(f"Error al actualizar restaurante: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# ------------------------------
# AGREGATION
# ------------------------------

# Top restaurantes (mejor calificacion)
def convert_object_ids(obj):
    if isinstance(obj, dict):
        return {k: convert_object_ids(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_object_ids(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj

@app.post("/agg/top-res/")
async def top_restaurantes():
    try:
        db = get_db()
        cursor = db.restaurantes.aggregate([
            {"$sort": {"calificacionPromedio": -1}},
            {"$limit": 10}
        ])
        res = await cursor.to_list() 
        parsed = convert_object_ids(res)
        return parsed
    except Exception as e:
        print(f"Error obteniendo top restaurantes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Top articulos (mas vendidos)
@app.post("/agg/top-dish/")
async def top_platos():
    try:
        db = get_db()
        cursor = db.ordenes.aggregate([
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.articulo_id",
                "total_sales": {"$sum": "$items.cantidad"}
            }},
            {"$sort": {"total_sales": -1}},
            {"$limit": 10},
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
            { "$unwind": "$articulo" },
            {"$project": {
                "total_sales": 1,
                "articulo": 1
            }}
        ])
        
        res = await cursor.to_list() 
        parsed = convert_object_ids(res)
        return parsed
        
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
        parsed = convert_object_ids(res)
        return parsed
        
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
            {"$project": {
                "user_info": "$user_info",
                "order_info": "$order_info",
                "comentario": "$comentario",
                "calificacion": "&calificacion",
                "fecha": "$fecha"
            }}
        ])
        
        res = await cursor.to_list() 
        parsed = convert_object_ids(res)
        return parsed
        
    except Exception as e:
        print(f"Error obteniendo top restaurantes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
# ----------------------------
# Bulk Write
# ----------------------------
@app.post("/bulk-create/{collection}")
async def bulk_create(collection: str, docs: list[dict]):
    parsed_docs = []
    ## Collection is valid
    if collection not in ["restaurantes","ordenes","articulos","usuarios","resenias"]:
        raise HTTPException(
            status_code=422,
            detail=f"Collection '{collection}' not found"
        )
    
    ## Docs arent Empty:
    if not docs:
        raise HTTPException(
            status_code=422,
            detail=f"No docs found to be inserted"
        )
    
    ## Docs are correct
    if collection == "restaurantes":
        try:
            parsed_docs = [Restaurante(**d) for d in docs]
        except ValidationError as e:
            # e.errors() gives a list of detailed validation issues
            raise HTTPException(
                status_code=422,
                detail=f"Validation failed: {e.errors()}"
            )

    # elif collection == "ordenes":
    #     pass
    # elif collection == "resenias":
    #     pass
    # elif collection == "usuarios":
    #     pass
    # elif collection == "articulos":
    #     pass
    else: ## Raise exception
        raise HTTPException(status_code=500, detail="Bulk update failed")
        

    # Generating operations:
    operations = [InsertOne(doc) for doc in parsed_docs]
    # Executing operations:
    try:
        result = await db[collection].bulk_write(operations)
        return {
            "inserted_count": result.inserted_count
        }
    except Exception as e:
        print(f"Bulk update error: {e}")
        raise HTTPException(status_code=500, detail="Bulk update failed")
    
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
@app.post("/usuarios/filtrar")
async def filtrar_usuarios(
    filtro: dict = Body(...),
    projection: Optional[List[str]] = Query(None, description="Campos a incluir en la respuesta"),
    sort: Optional[str] = Query(None, description="Campo:asc|desc"),
    skip: int = 0,
    limit: int = 10
):
    try:
        db = get_db()
        proj_dict = {f.strip(): 1 for f in projection[0].split(",")} if projection else None

        cursor = db.usuarios.find(filtro, proj_dict)

        if sort:
            campo, orden = sort.split(":")
            cursor = cursor.sort(campo, 1 if orden == "asc" else -1)

        cursor = cursor.skip(skip).limit(limit)
        usuarios = await cursor.to_list(length=limit)

        for u in usuarios:
            u["_id"] = str(u["_id"])

        return usuarios
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

# ------------------------------
# CRUD ARTICULOS DEL MENU
# ------------------------------

@app.post("/articulos/")
async def crear_articulo(articulo: Articulo):
    try:
        db = get_db()
        res = await db.articulos.insert_one(articulo.dict())
        return {"id": str(res.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/articulos/")
async def listar_articulos(nombre: str = None, categoria: str = None, restaurante_id: str = None, disponible: bool = None):
    try:
        db = get_db()
        filtro = {}
        if nombre:
            filtro["nombre"] = {"$regex": nombre, "$options": "i"}
        if categoria:
            filtro["categorias"] = categoria
        if restaurante_id:
            filtro["restaurante_id"] = restaurante_id
        if disponible in [True, False]:
            filtro["disponible"] = disponible

        articulos = await db.articulos.find(filtro).to_list(100)
        for a in articulos:
            a["_id"] = str(a["_id"])
            if "restaurante_id" in a and isinstance(a["restaurante_id"], ObjectId):
                a["restaurante_id"] = str(a["restaurante_id"])
        return articulos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/articulos/{id}")
async def obtener_articulo(id: str):
    try:
        db = get_db()
        a = await db.articulos.find_one({"_id": ObjectId(id)})
        if not a: raise HTTPException(status_code=404, detail="Artículo no encontrado")
        parsed = convert_object_ids(a)
        return parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/articulos/filtrar")
async def filtrar_articulos(
    filtro: dict = Body(...),
    projection: Optional[List[str]] = Query(None, description="Campos a incluir en la respuesta"),
    sort: Optional[str] = Query(None, description="Campo:asc|desc"),
    skip: int = 0,
    limit: int = 10
):
    try:
        db = get_db()

        # Parse projection
        if projection:
            if isinstance(projection, list) and len(projection) == 1 and "," in projection[0]:
                projection = projection[0].split(",")
            proj_dict = {f.strip(): 1 for f in projection}
        else:
            proj_dict = None

        # Convert restaurante_id a ObjectId si es string válido
        if "restaurante_id" in filtro and isinstance(filtro["restaurante_id"], str):
            try:
                filtro["restaurante_id"] = ObjectId(filtro["restaurante_id"])
            except:
                raise HTTPException(status_code=400, detail="restaurante_id no es un ObjectId válido")

        cursor = db.articulos.find(filtro, proj_dict)

        # Ordenamiento
        if sort:
            campo, orden = sort.split(":")
            cursor = cursor.sort(campo, 1 if orden == "asc" else -1)

        # Skip y limit
        cursor = cursor.skip(skip).limit(limit)
        articulos = await cursor.to_list(length=limit)

        for a in articulos:
            a["_id"] = str(a["_id"])
            if "restaurante_id" in a and isinstance(a["restaurante_id"], ObjectId):
                a["restaurante_id"] = str(a["restaurante_id"])

        return articulos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.put("/articulos/{id}")
async def actualizar_articulo(id: str, data: dict):
    try:
        db = get_db()
        res = await db.articulos.update_one({"_id": ObjectId(id)}, {"$set": data})
        return {"modificados": res.modified_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/articulos/{id}")
async def eliminar_articulo(id: str):
    try:
        db = get_db()
        res = await db.articulos.delete_one({"_id": ObjectId(id)})
        return {"eliminados": res.deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ------------------------------
#  MANEJO DE ARRAYS
# ------------------------------

from pydantic import BaseModel, ValidationError

class CategoriaInput(BaseModel):
    categoria: str

class IDInput(BaseModel):
    articulo_id: str

class ReseniaInput(BaseModel):
    resenia_id: str

class ImagenInput(BaseModel):
    imagen_id: str

@app.patch("/restaurantes/{id}/add-categoria")
async def agregar_categoria(id: str, data: CategoriaInput):
    db = get_db()
    res = await db.restaurantes.update_one(
        {"_id": ObjectId(id)},
        {"$addToSet": {"categorias": data.categoria}}
    )
    return {"modificados": res.modified_count}

@app.patch("/restaurantes/{id}/remove-categoria")
async def quitar_categoria(id: str, data: CategoriaInput):
    db = get_db()
    res = await db.restaurantes.update_one(
        {"_id": ObjectId(id)},
        {"$pull": {"categorias": data.categoria}}
    )
    return {"modificados": res.modified_count}

@app.patch("/restaurantes/{id}/add-menu")
async def agregar_articulo_menu(id: str, data: IDInput):
    db = get_db()
    res = await db.restaurantes.update_one(
        {"_id": ObjectId(id)},
        {"$addToSet": {"menu": ObjectId(data.articulo_id)}}
    )
    return {"modificados": res.modified_count}

@app.patch("/restaurantes/{id}/remove-menu")
async def quitar_articulo_menu(id: str, data: IDInput):
    db = get_db()
    res = await db.restaurantes.update_one(
        {"_id": ObjectId(id)},
        {"$pull": {"menu": ObjectId(data.articulo_id)}}
    )
    return {"modificados": res.modified_count}

@app.patch("/restaurantes/{id}/add-resenia")
async def agregar_resenia_restaurante(id: str, data: ReseniaInput):
    db = get_db()
    res = await db.restaurantes.update_one(
        {"_id": ObjectId(id)},
        {"$addToSet": {"resenias": ObjectId(data.resenia_id)}}
    )
    return {"modificados": res.modified_count}

@app.patch("/restaurantes/{id}/remove-resenia")
async def quitar_resenia_restaurante(id: str, data: ReseniaInput):
    db = get_db()
    res = await db.restaurantes.update_one(
        {"_id": ObjectId(id)},
        {"$pull": {"resenias": ObjectId(data.resenia_id)}}
    )
    return {"modificados": res.modified_count}

@app.patch("/articulos/{id}/add-imagen")
async def agregar_imagen_articulo(id: str, data: ImagenInput):
    db = get_db()
    res = await db.articulos.update_one(
        {"_id": ObjectId(id)},
        {"$push": {"imagenes": ObjectId(data.imagen_id)}}
    )
    return {"modificados": res.modified_count}

@app.patch("/articulos/{id}/remove-imagen")
async def quitar_imagen_articulo(id: str, data: ImagenInput):
    db = get_db()
    res = await db.articulos.update_one(
        {"_id": ObjectId(id)},
        {"$pull": {"imagenes": ObjectId(data.imagen_id)}}
    )
    return {"modificados": res.modified_count}
