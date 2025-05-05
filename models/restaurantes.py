
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Literal, Union

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
    simple_filter: Optional[Dict[str, Union[str, float]]] = None
    simple_sort: Optional[Dict[str, Literal[1,-1]]] = None
    limit: Optional[int] = None
    skip: Optional[int] = None
    categories: Optional[List[str]] = None
    