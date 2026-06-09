from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    jugador = relationship("Jugador", back_populates="user", uselist=False)
    servers = relationship("Server", back_populates="owner", cascade="all, delete-orphan")
    ship = relationship("Ship", back_populates="owner", uselist=False)