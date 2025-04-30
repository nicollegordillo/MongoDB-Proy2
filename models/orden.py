from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .base import PyObjectId

class ItemOrden(BaseModel):
    articulo_id: PyObjectId = Field(...)
    nombre: str
    cantidad: int
    precioUnitario: float

class Orden(BaseModel):
    usuario_id: PyObjectId = Field(...)
    restaurante_id: PyObjectId = Field(...)
    fecha: datetime
    estado: str
    total: float
    items: List[ItemOrden]
    resenia_id: Optional[PyObjectId] = None
