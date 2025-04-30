from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ItemOrden(BaseModel):
    articulo_id: str
    nombre: str
    cantidad: int
    precioUnitario: float

class Orden(BaseModel):
    usuario_id: str
    restaurante_id: str
    fecha: datetime
    estado: str
    total: float
    items: List[ItemOrden]
    resenia_id: Optional[str] = None
