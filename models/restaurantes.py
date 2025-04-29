
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class Coordenadas(BaseModel):
    type: str
    coordinates: List[float]  

class Direccion(BaseModel):
    calle: str
    zona: int
    coordenadas: Coordenadas

class Restaurante(BaseModel):
    restaurante_id: str
    nombre: str
    direccion: Direccion
    categorias: List[str]
    menu: List[str]
    calificacionPromedio: float
    resenias: List[str]
