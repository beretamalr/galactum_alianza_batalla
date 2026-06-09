# app/schemas/misiones.py
from pydantic import BaseModel
from typing import List, Any

class MisionReclamarPeticion(BaseModel):
    mision_id: str

class MisionReclamarRespuesta(BaseModel):
    status: str
    message: str
    recursos_ganados: List[Any] # Usar un schema más específico si se define para recursos

class MisionItem(BaseModel):
    mision_id: str
    titulo: str
    descripcion: str
    progreso_actual: int
    cantidad_requerida: int
    estado: str
    recompensa: List[Any] # Usar un schema más específico si se define para recursos

class MisionesResponse(BaseModel):
    status: str
    misiones_diarias: List[MisionItem]
    misiones_historia: List[MisionItem]