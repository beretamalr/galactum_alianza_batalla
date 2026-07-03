from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base import Base


class Jugador(Base):
    __tablename__ = "jugadores"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    alliance_id = Column(Integer, ForeignKey("alliances.id"), nullable=True)
    power = Column(Integer, nullable=False, default=5000)

    user = relationship("User", back_populates="jugador")
    alliance = relationship(
        "Alliance",
        back_populates="members",
        foreign_keys=[alliance_id],
    )
    alliance_join_requests = relationship(
        "AllianceJoinRequest",
        back_populates="applicant",
        foreign_keys="AllianceJoinRequest.applicant_jugador_id",
        cascade="all, delete-orphan",
    )

    inventory = relationship("Inventory", back_populates="jugador", cascade="all, delete-orphan")
    ship_rooms = relationship("ShipRoom", back_populates="jugador", cascade="all, delete-orphan")
    tripulantes = relationship("Tripulante", back_populates="jugador", cascade="all, delete-orphan")
