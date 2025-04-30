from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .base import PyObjectId  # Asegúrate que está bien importado
from bson import ObjectId

class ItemOrden(BaseModel):
    articulo_id: PyObjectId = Field(...)
    nombre: str
    cantidad: int
    precioUnitario: float

class Orden(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    usuario_id: PyObjectId = Field(...)
    restaurante_id: PyObjectId = Field(...)
    fecha: datetime
    estado: str
    total: float
    items: List[ItemOrden]
    resenia_id: Optional[PyObjectId] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

