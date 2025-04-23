from pydantic import BaseModel
from datetime import datetime

class Resenia(BaseModel):
    usuario_id: str
    restaurante_id: str
    orden_id: str
    comentario: str
    calificacion: int
    fecha: datetime
