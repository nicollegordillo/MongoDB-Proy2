from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic.json import ENCODERS_BY_TYPE
from typing import Optional
import bson

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not bson.ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return bson.ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Opcional: para que se serialice correctamente al usar .json()
ENCODERS_BY_TYPE[ObjectId] = str
