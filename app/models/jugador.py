from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, ForeignKey, Integer
from app.db.base import Base
from sqlalchemy.orm import relationship

class Jugador(Base):
    __tablename__ = "jugadores"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)

    user = relationship("User", back_populates="jugador")
    
    inventory = relationship("Inventory", back_populates="jugador", cascade="all, delete-orphan")
    ship_rooms = relationship("ShipRoom", back_populates="jugador", cascade="all, delete-orphan")
    tripulantes = relationship("Tripulante", back_populates="jugador", cascade="all, delete-orphan")