from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class MisionMaestra(Base):
    """
    Plantilla de misión disponible para todos los jugadores.

    La misión define qué recurso se debe conseguir y qué recompensa entrega.
    El progreso real por jugador queda en MisionJugador.
    """
    __tablename__ = "misiones_maestras"

    mision_id = Column(String, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo_mision = Column(String, nullable=False, default="diaria")
    dificultad = Column(String, nullable=False, default="Fácil")

    tipo_objetivo = Column(String, nullable=False, default="tener_recurso")
    objetivo_recurso_id = Column(Integer, ForeignKey("catalogo_items.id"), nullable=True)
    cantidad_requerida = Column(Integer, nullable=False, default=1)

    recompensa_data = Column(Text, nullable=False, default="[]")
    activa = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    objetivo_recurso = relationship("CatalogoItem", foreign_keys=[objetivo_recurso_id])
    jugadores = relationship("MisionJugador", back_populates="mision_maestra")


class MisionJugador(Base):
    """
    Estado de una misión para un jugador específico.

    Estados usados por Godot:
    - activa: aceptada, pero aún no cumple el requisito.
    - completada: cumple el requisito y puede reclamar recompensa.
    - reclamada: la recompensa ya fue entregada.
    """
    __tablename__ = "misiones_jugadores"
    __table_args__ = (
        UniqueConstraint("jugador_id", "mision_id", name="uq_mision_jugador_unica"),
    )

    id = Column(Integer, primary_key=True, index=True)
    jugador_id = Column(Integer, ForeignKey("jugadores.id"), nullable=False)
    mision_id = Column(String, ForeignKey("misiones_maestras.mision_id"), nullable=False)
    progreso_actual = Column(Integer, nullable=False, default=0)
    estado = Column(String, nullable=False, default="activa")
    aceptada_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    reclamada_en = Column(DateTime(timezone=True), nullable=True)

    mision_maestra = relationship("MisionMaestra", back_populates="jugadores")
