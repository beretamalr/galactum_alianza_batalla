# app/schemas/unidades.py
from pydantic import BaseModel

class UnitCreateRequest(BaseModel):
    unit_type_id: str # Ej: "Infanteria", "Drones"
    quantity: int = 1 # Por defecto, crear 1 unidad

class UnitCreateResponse(BaseModel):
    status: str
    message: str
    unit_type_id: str
    created_quantity: int