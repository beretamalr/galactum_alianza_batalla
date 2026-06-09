# app/schemas/tripulantes.py
from pydantic import BaseModel

class TripulanteContratarPeticion(BaseModel):
    tripulante_id: str

class TripulanteMejorarPeticion(BaseModel):
    # Asumo que el jugador tiene un ID único por cada tripulante en su inventario
    tripulante_instancia_id: int 
    nivel_objetivo: int

class TripulanteAccionRespuesta(BaseModel):
    status: str
    message: str