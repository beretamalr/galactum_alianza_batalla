# app/models/player_equipment.py
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.db.base import Base

class PlayerEquipment(Base):
    __tablename__ = "player_equipment"
    __table_args__ = (UniqueConstraint('player_id', 'item_id', name='_player_item_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("jugadores.id"), nullable=False)
    item_id = Column(String, nullable=False) # Ej: "LaserBasico", "EscudoMK1"
    quantity = Column(Integer, default=1, nullable=False)