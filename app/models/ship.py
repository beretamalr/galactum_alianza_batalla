# app/models/ship.py - CORREGIDO
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Column, Float, Boolean, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base

class Ship(Base):
    __tablename__ = "ships"
    # Corrección: Se elimina la definición duplicada de 'id' y se mantiene la correcta (UUID).
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    is_moving = Column(Boolean, default=False)
    current_pos_x = Column(Float)
    current_pos_y = Column(Float)
    start_pos_x = Column(Float, nullable=True)
    start_pos_y = Column(Float, nullable=True)
    end_pos_x = Column(Float, nullable=True)
    end_pos_y = Column(Float, nullable=True)

    # ¡¡NUEVAS COLUMNAS!!
    movement_start_time = Column(DateTime, nullable=True)
    estimated_arrival_time = Column(DateTime, nullable=True)
    
    speed = Column(Float, default=100.0) # Velocidad base de la nave (unidades/segundo)
    
    # --- Nuevos Atributos de Estadísticas Base ---
    
    # cargo_capacity = Column(Integer, default=1000) # Capacidad total de almacenamiento de recursos de la nave
    # shield_points = Column(Integer, default=100) # Puntos de escudo de la nave
    # hull_points = Column(Integer, default=500) # Puntos de vida estructurales del casco de la nave
    # extractor_level = Column(Integer, default=1) # Representa la salud total de la nave después de que los escudos se agotan
    # weapon_slots = Column(Integer, default=2) # 
    # crew_slots = Column(Integer, default=4)

    # Relación
    owner = relationship("User", back_populates="ship")