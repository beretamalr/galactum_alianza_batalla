# En app/schemas/player.py

from pydantic import BaseModel
from typing import List, Optional

# --- ¡ESTA ES LA PARTE A MODIFICAR! ---
class InventoryItem(BaseModel):
    resource_id: int
    quantity: int
    # Añadimos los campos opcionales para el nombre y la descripción.
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo: Optional[str] = None
    rareza: Optional[str] = None
    imagen_url: Optional[str] = None


    # Esto es importante para que Pydantic pueda leer desde objetos de SQLAlchemy si es necesario.
    class Config:
        from_attributes = True

class InventoryResponse(BaseModel):
    # Esta parte probablemente ya está bien.
    recursos: List[InventoryItem]


class RoomStatus(BaseModel):
    room_id: str
    level: int    