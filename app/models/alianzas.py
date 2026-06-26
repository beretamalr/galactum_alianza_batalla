from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.base import Base  # O como importes tu Base de SQLAlchemy

class Alliance(Base):
    __tablename__ = "alliances"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    level = Column(Integer, default=1)           # ¡En inglés para PostgreSQL!
    members_count = Column(Integer, default=1)
    max_members = Column(Integer, default=100)
    power = Column(String, default="0")
    lang = Column(String, default="ES")
    puntos_prestigio = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())