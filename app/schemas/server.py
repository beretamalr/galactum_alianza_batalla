# app/schemas/server.py
from pydantic import BaseModel
from uuid import UUID

class ServerBase(BaseModel):
    name: str
    region: str

class ServerCreate(ServerBase):
    """Payload para crear servidor."""
    pass

class ServerUpdate(BaseModel):
    """Payload para actualizar servidor (parcial)."""
    name: str | None = None
    region: str | None = None

class ServerOut(ServerBase):
    """Respuesta pública de servidor."""
    id: UUID
    owner_id: UUID

    class Config:
        from_attributes = True  # Pydantic v2 reemplaza orm_mode

class Server(ServerBase):
    id: UUID
    owner_id: UUID

    class Config:
        from_attributes = True
