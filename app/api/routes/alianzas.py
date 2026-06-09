# app/v2_features_beta/schemas/alianzas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Schemas de Miembros ---
class MiembroAlianzaBase(BaseModel):
    username: str # Asumimos que cargamos el username desde el modelo Jugador
    rol: str

    class Config:
        from_attributes = True

# --- Schemas de Alianza ---
class AlianzaCrearPeticion(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=30)
    tag: str = Field(..., min_length=2, max_length=5)
    descripcion: Optional[str] = Field(None, max_length=255)

class AlianzaRespuesta(BaseModel):
    alianza_id: int
    nombre: str
    tag: str
    puntos_prestigio: int
    miembros: List[MiembroAlianzaBase]

    class Config:
        from_attributes = True

# --- Schemas de Asedio ---
class AsedioIniciarRespuesta(BaseModel):
    status: str
    message: str
    asedio_id: int
    fecha_fin: datetime

class UnidadRefuerzo(BaseModel):
    tipo: str
    quantity: int

class RefuerzoEnviarPeticion(BaseModel):
    unidades_enviadas: List[UnidadRefuerzo]

class RefuerzoEnviarRespuesta(BaseModel):
    status: str
    message: str