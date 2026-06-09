from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint('player_id', 'resource_id', name='_player_resource_uc'),)
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey('jugadores.id'), nullable=False)
    resource_id = Column(Integer, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    
    jugador = relationship("Jugador", back_populates="inventory")