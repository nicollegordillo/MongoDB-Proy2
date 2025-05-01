from pydantic import BaseModel
from typing import List

class Articulo(BaseModel):
    restaurante_id: str
    nombre: str
    descripcion: str
    categorias: List[str]
    precio: float
    disponible: bool
    imagenes: List[str] = []