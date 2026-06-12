# app/models/asteroid.py
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Asteroid(Base):
    __tablename__ = "asteroids"

    id: Mapped[int] = mapped_column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # El ID lógico del juego (ej: "ast_1234")
    asteroid: Mapped[str] = mapped_column("asteroid", String, unique=True, index=True, nullable=False)
    
    # Coordenadas
    position_x: Mapped[float] = mapped_column("pos_x", Float, nullable=False)
    position_y: Mapped[float] = mapped_column("pos_y", Float, nullable=False)
    
    # Recursos
    resource_id: Mapped[int] = mapped_column(Integer,ForeignKey("catalogo_items.id"), nullable=False)
    cantidad_restante: Mapped[int] = mapped_column("cantidad_restante", Integer, nullable=False, default=3)

    # --- AGREGADOS NECESARIOS PARA LA LÓGICA DE JUEGO ---
    
    # Cantidad máxima original (para saber cuánto ponerle al revivirlo)
    cantidad_maxima: Mapped[int] = mapped_column("cantidad_maxima", Integer, default=100)
    
    # Estado de vida: True = Visible, False = Destruido (Cooldown)
    is_active: Mapped[bool] = mapped_column("is_active", Boolean, default=True)
    
    # Fecha de resurrección (Solo si is_active es False)
    reaparecer_en: Mapped[Optional[datetime]] = mapped_column("reaparecer_en", DateTime, nullable=True)

    # --- AGREGADOS PARA EL BLOQUEO DE MINADO ---

    # Quién lo está minando actualmente
    mined_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        "mined_by_id",
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )

    # Cuándo termina el minado
    mining_finish_at: Mapped[Optional[datetime]] = mapped_column("mining_finish_at", DateTime, nullable=True)