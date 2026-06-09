# app/v2_features_beta/schemas/conflicto.py
from pydantic import BaseModel
from typing import List

class UnidadAtaque(BaseModel):
    type: str # "Infanteria", "Drones", etc.
    quantity: int

class FuerzaAtaque(BaseModel):
    units: List[UnidadAtaque]
    assigned_crew_ids: List[str] # Ej: ["crew_id_1", "crew_id_7"]

class PeticionResolverConflicto(BaseModel):
    target_username: str
    attacking_force: FuerzaAtaque

# --- Respuesta ---
class PerdidasUnidad(BaseModel):
    type: str
    quantity: int

class RecursosGanados(BaseModel):
    id: str
    quantity: int

class RespuestaResolverConflicto(BaseModel):
    status: str
    outcome: str # "win" o "loss"
    conflict_id: str
    attacker_losses: List[PerdidasUnidad]
    defender_losses: List[PerdidasUnidad]
    resources_gained: List[RecursosGanados]