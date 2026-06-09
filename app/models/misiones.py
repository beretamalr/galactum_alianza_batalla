# app/models/misiones.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class MisionMaestra(Base):
    """
    Define la plantilla de una misión (qué es, qué pide y qué da).
    """
    __tablename__ = "misiones_maestras"

    mision_id = Column(String, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    tipo_mision = Column(String, nullable=False) # 'diaria' o 'historia'
    cantidad_requerida = Column(Integer, nullable=False)
    recompensa_data = Column(String, nullable=False) # JSON String: '[{"id": "Ore", "quantity": 10}]'

class MisionJugador(Base):
    """
    Registra el progreso de un jugador en una misión específica.
    """
    __tablename__ = "misiones_jugadores"

    id = Column(Integer, primary_key=True, index=True)
    jugador_id = Column(Integer, ForeignKey("jugadores.id"), nullable=False)
    mision_id = Column(String, ForeignKey("misiones_maestras.mision_id"), nullable=False)
    progreso_actual = Column(Integer, default=0)
    estado = Column(String, default="activa") # 'activa', 'completada', 'reclamada'

    mision_maestra = relationship("MisionMaestra")