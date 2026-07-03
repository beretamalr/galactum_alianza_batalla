from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Alliance(Base):
    __tablename__ = "alliances"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    members_count = Column(Integer, default=1, nullable=False)
    max_members = Column(Integer, default=100, nullable=False)
    power = Column(String, default="0", nullable=False)
    lang = Column(String, default="ES", nullable=False)
    puntos_prestigio = Column(Integer, default=0, nullable=False)
    required_power = Column(Integer, default=0, nullable=False)

    # El fundador queda registrado como líder de la alianza.
    leader_jugador_id = Column(
        Integer,
        ForeignKey("jugadores.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = Column(DateTime, server_default=func.now())

    # Se indica foreign_keys porque Alliance también referencia Jugador mediante leader_jugador_id.
    members = relationship(
        "Jugador",
        back_populates="alliance",
        foreign_keys="Jugador.alliance_id",
    )
    leader = relationship("Jugador", foreign_keys=[leader_jugador_id], post_update=True)
    join_requests = relationship(
        "AllianceJoinRequest",
        back_populates="alliance",
        cascade="all, delete-orphan",
    )


class AllianceJoinRequest(Base):
    __tablename__ = "alliance_join_requests"

    id = Column(Integer, primary_key=True, index=True)
    alliance_id = Column(
        Integer,
        ForeignKey("alliances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applicant_jugador_id = Column(
        Integer,
        ForeignKey("jugadores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    reviewed_by_jugador_id = Column(
        Integer,
        ForeignKey("jugadores.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)

    alliance = relationship("Alliance", back_populates="join_requests")
    applicant = relationship(
        "Jugador",
        back_populates="alliance_join_requests",
        foreign_keys=[applicant_jugador_id],
    )
    reviewed_by = relationship("Jugador", foreign_keys=[reviewed_by_jugador_id])
