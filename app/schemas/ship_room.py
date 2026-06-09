# app/schemas/ship_room.py
from pydantic import BaseModel

class ShipRoomOut(BaseModel):
    """Schema para devolver la información de una sala de la nave."""
    room_id: str
    level: int

    class Config:
        from_attributes = True