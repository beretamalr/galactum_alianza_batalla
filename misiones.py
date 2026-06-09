# app/models/misiones.py
from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
# ¡Revisa esta importación! Debe apuntar a mi Base de SQLAlchemy
from app.db.base import Base

class MisionMaestra(Base):
    __tablename__ = "misiones_maestras"
    
    mision_id = Column(String, primary_key=True, index=True)
    tipo_mision = Column(Enum('diaria', 'semanal', 'historia', name='tipo_mision_enum'), nullable=False)
    titulo = Column(String, nullable=False)
    descripcion = Column(String)
    tipo_objetivo = Column(Enum('minar_recurso', 'construir_sala', 'ganar_conflicto', name='tipo_objetivo_enum'), nullable=False)
    objetivo_id_requerido = Column(String) # Ej: "Roderitium" o "Armeria"
    cantidad_requerida = Column(Integer, default=1)
    recompensa_data = Column(String) # JSON String, ej: '[{"id": "Kliptium", "quantity": 100}]'

class MisionJugador(Base):
    __tablename__ = "misiones_jugadores"
    
    mision_jugador_id = Column(Integer, primary_key=True, index=True)
    jugador_id = Column(Integer, ForeignKey('jugadores.id'))
    mision_id = Column(String, ForeignKey('misiones_maestras.mision_id'))
    progreso_actual = Column(Integer, default=0)
    estado = Column(Enum('activa', 'completada', 'reclamada', name='estado_mision_enum'), default='activa')
    
    mision_maestra = relationship("MisionMaestra")