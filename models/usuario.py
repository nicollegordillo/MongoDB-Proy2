from pydantic import BaseModel
from typing import Optional

class DireccionUsuario(BaseModel):
    calle: str
    zona: int
    ciudad: str

class Usuario(BaseModel):
    nombre: str
    correo: str
    telefono: str
    direccion: DireccionUsuario
    tipo: str