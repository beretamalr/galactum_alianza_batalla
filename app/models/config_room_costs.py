# app/models/config_room_costs.py
from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.db.base import Base

class ConfigRoomCost(Base):
    __tablename__ = "config_room_costs"
    __table_args__ = (UniqueConstraint('room_id', 'target_level', name='_room_level_cost_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, nullable=False)
    target_level = Column(Integer, nullable=False)
    cost_data = Column(String, nullable=False) # JSON String: '[{"id": "Ore", "quantity": 100}]'