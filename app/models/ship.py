from sqlalchemy.dialects.postgresql import UUID
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Ship(Base):
    __tablename__ = "ships"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Identidad de la nave
    name = Column(
        String(80),
        nullable=False,
        default="Ares Explorer",
    )

    level = Column(
        Integer,
        nullable=False,
        default=1,
    )

    # Estado operativo visible en la pantalla Mi Nave
    energy_current = Column(
        Integer,
        nullable=False,
        default=100,
    )

    energy_max = Column(
        Integer,
        nullable=False,
        default=100,
    )

    shield_current = Column(
        Integer,
        nullable=False,
        default=100,
    )

    shield_max = Column(
        Integer,
        nullable=False,
        default=100,
    )

    hull_current = Column(
        Integer,
        nullable=False,
        default=500,
    )

    hull_max = Column(
        Integer,
        nullable=False,
        default=500,
    )

    # Estadísticas base para evolución futura
    cargo_capacity = Column(
        Integer,
        nullable=False,
        default=1000,
    )

    extractor_level = Column(
        Integer,
        nullable=False,
        default=1,
    )

    weapon_slots = Column(
        Integer,
        nullable=False,
        default=2,
    )

    crew_slots = Column(
        Integer,
        nullable=False,
        default=4,
    )

    # Estado de movimiento y mapa
    is_moving = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    current_pos_x = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    current_pos_y = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    start_pos_x = Column(
        Float,
        nullable=True,
    )

    start_pos_y = Column(
        Float,
        nullable=True,
    )

    end_pos_x = Column(
        Float,
        nullable=True,
    )

    end_pos_y = Column(
        Float,
        nullable=True,
    )

    movement_start_time = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    estimated_arrival_time = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    speed = Column(
        Float,
        nullable=False,
        default=100.0,
    )

    owner = relationship(
        "User",
        back_populates="ship",
    )