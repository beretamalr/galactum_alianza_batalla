from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


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
    startPosition: Position
    endPosition: Position
    movementStartTime: datetime
    estimatedArrivalTime: datetime


class ShipMoveResponse(BaseModel):
    status: str
    message: str
    data: ShipMoveResponseData


class RoomUpgradeRequest(BaseModel):
    room_id: str
    target_level: int


class RoomUpgradeResponse(BaseModel):
    status: str
    message: str
    room_id: str
    new_level: int


# ---------------------------------------------------------
# Schemas para GET /ship/estado
# ---------------------------------------------------------

class ShipOverview(BaseModel):
    id: UUID
    nombre: str
    nivel: int

    energia_actual: int
    energia_maxima: int

    escudo_actual: int
    escudo_maximo: int

    casco_actual: int
    casco_maximo: int

    capacidad_carga: int
    nivel_extractor: int
    espacios_armas: int
    espacios_tripulacion: int

    posicion: Position
    en_movimiento: bool
    velocidad: float


class ShipStateResponse(BaseModel):
    comandante: str
    nave: ShipOverview