
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Literal

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

# Para los queries 

class RestauranteOptions(BaseModel):
    simple_filter: Optional[Dict[Literal["nombre", "calificacionPromedio"], str]]
    simple_sort: Optional[Dict[str, Literal[1,-1]]]
    limit: Optional[int]
    skip: Optional[int]
    categories: Optional[List[str]]
    