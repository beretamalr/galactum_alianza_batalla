# app/schemas/ship.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Position(BaseModel):
    x: float
    y: float

class ShipStatus(BaseModel):
    username: str
    isMoving: bool
    currentPosition: Position
    startPosition: Optional[Position] = None
    endPosition: Optional[Position] = None
    movementStartTime: Optional[datetime] = None
    estimatedArrivalTime: Optional[datetime] = None

class ShipsResponse(BaseModel):
    status: str = "success"
    data: List[ShipStatus]

class ShipMoveRequest(BaseModel):
    targetPosition: Position

class ShipMoveResponseData(BaseModel):
    startPosition: Position        # Posición inicial (x, y)
    endPosition: Position
    movementStartTime: datetime    # Hora exacta de inicio
    estimatedArrivalTime: datetime

class ShipMoveResponse(BaseModel):
    status: str
    message: str
    data: ShipMoveResponseData

# --- Schemas para Mejora de Salas ---
class RoomUpgradeRequest(BaseModel):
    room_id: str
    target_level: int

class RoomUpgradeResponse(BaseModel):
    status: str
    message: str
    room_id: str
    new_level: int