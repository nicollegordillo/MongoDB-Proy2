from fastapi import APIRouter, HTTPException
from bson import ObjectId
from database import db

router = APIRouter()

@router.post("/")
async def crear_resenia(resenia: dict):
    res = await db.resenias.insert_one(resenia)
    return {"id": str(res.inserted_id)}

@router.get("/")
async def listar_resenias():
    resenias = await db.resenias.find().to_list(100)
    for r in resenias:
        r["_id"] = str(r["_id"])
    return resenias

@router.get("/{id}")
async def obtener_resenia(id: str):
    r = await db.resenias.find_one({"_id": ObjectId(id)})
    if not r:
        raise HTTPException(404)
    r["_id"] = str(r["_id"])
    return r

@router.put("/{id}")
async def actualizar_resenia(id: str, data: dict):
    res = await db.resenias.update_one({"_id": ObjectId(id)}, {"$set": data})
    return {"modificados": res.modified_count}

@router.delete("/{id}")
async def eliminar_resenia(id: str):
    res = await db.resenias.delete_one({"_id": ObjectId(id)})
    return {"eliminados": res.deleted_count}
