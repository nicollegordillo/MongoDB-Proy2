from fastapi import APIRouter, HTTPException, Request
from bson import ObjectId

router = APIRouter()

@router.post("/")
async def crear_orden(request: Request, orden: dict):
    db = request.app.state.db
    res = await db.ordenes.insert_one(orden)
    return {"id": str(res.inserted_id)}

@router.get("/")
async def listar_ordenes(request: Request, skip: int = 0, limit: int = 10):
    try:
        db = request.app.state.db
        ordenes = await db.ordenes.find().skip(skip).limit(limit).to_list(100)
        for o in ordenes:
            o["_id"] = str(o["_id"])
        return ordenes
    except Exception as e:
        print("Error en listar_ordenes:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}")
async def obtener_orden(request: Request, id: str):
    db = request.app.state.db
    orden = await db.ordenes.find_one({"_id": ObjectId(id)})
    if not orden:
        raise HTTPException(404)
    orden["_id"] = str(orden["_id"])
    return orden

@router.put("/{id}")
async def actualizar_estado(request: Request, id: str, estado: str):
    db = request.app.state.db
    res = await db.ordenes.update_one({"_id": ObjectId(id)}, {"$set": {"estado": estado}})
    return {"modificados": res.modified_count}

@router.delete("/{id}")
async def eliminar_orden(request: Request, id: str):
    db = request.app.state.db
    res = await db.ordenes.delete_one({"_id": ObjectId(id)})
    return {"eliminados": res.deleted_count}

