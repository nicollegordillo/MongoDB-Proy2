# base.py
from bson import ObjectId
from pydantic import BaseModel
from pydantic.json import ENCODERS_BY_TYPE

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("ID no válido")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Para que Pydantic serialice ObjectId correctamente
ENCODERS_BY_TYPE[ObjectId] = str
