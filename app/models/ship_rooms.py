from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.db.base import Base
from sqlalchemy.orm import relationship

class ShipRoom(Base):
    __tablename__ = "ship_rooms"
    __table_args__ = (UniqueConstraint('player_id', 'room_id', name='_player_room_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey('jugadores.id'), nullable=False)
    room_id = Column(String, nullable=False) # Ej: "EngineRoom", "Bridge"
    level = Column(Integer, default=1, nullable=False)

    jugador = relationship("Jugador", back_populates="ship_rooms")
    tripulante = relationship("Tripulante", uselist=False, back_populates="room")