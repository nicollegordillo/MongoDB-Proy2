from fastapi import APIRouter, HTTPException
from bson import ObjectId
from database import db

router = APIRouter()

@router.post("/")
async def crear_orden(orden: dict):
    res = await db.ordenes.insert_one(orden)
    return {"id": str(res.inserted_id)}

@router.get("/")
async def listar_ordenes(skip: int = 0, limit: int = 10):
    ordenes = await db.ordenes.find().skip(skip).limit(limit).to_list(100)
    for o in ordenes:
        o["_id"] = str(o["_id"])
    return ordenes

@router.get("/{id}")
async def obtener_orden(id: str):
    orden = await db.ordenes.find_one({"_id": ObjectId(id)})
    if not orden:
        raise HTTPException(404)
    orden["_id"] = str(orden["_id"])
    return orden

@router.put("/{id}")
async def actualizar_estado(id: str, estado: str):
    res = await db.ordenes.update_one({"_id": ObjectId(id)}, {"$set": {"estado": estado}})
    return {"modificados": res.modified_count}

@router.delete("/{id}")
async def eliminar_orden(id: str):
    res = await db.ordenes.delete_one({"_id": ObjectId(id)})
    return {"eliminados": res.deleted_count}
