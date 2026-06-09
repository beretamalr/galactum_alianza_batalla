# app/models/player_units.py
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.db.base import Base

class PlayerUnit(Base):
    __tablename__ = "player_units"
    __table_args__ = (UniqueConstraint('player_id', 'unit_id', name='_player_unit_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("jugadores.id"), nullable=False)
    unit_id = Column(String, nullable=False) # Ej: "Infanteria"
    quantity = Column(Integer, default=0, nullable=False)