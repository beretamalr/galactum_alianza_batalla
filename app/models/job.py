# app/models/job.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from ..db.base import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("jugadores.id"), nullable=False)
    job_type = Column(String, nullable=False) # ej: 'crafting', 'research'
    related_id = Column(String) # ej: el ID de la receta que se está crafteando
    completion_time = Column(DateTime, nullable=False)
    status = Column(String, default='pending') # pending, completed, claimed