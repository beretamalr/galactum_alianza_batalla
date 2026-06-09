# app/v2_features_beta/models/costos_tripulantes.py
from sqlalchemy import Column, Integer, String
from ...db.base import Base

class TripulanteCostoContratar(Base):
    __tablename__ = "tripulantes_costos_contratar"
    
    tripulante_id = Column(String, primary_key=True) # ID del tripulante (ej: "comandante_kael")
    costo_data = Column(String, nullable=False) # JSON String: '[{"id": "Roderitium", "qty": 5000}]'

class TripulanteCostoMejora(Base):
    __tablename__ = "tripulantes_costos_mejora"
    
    nivel_objetivo = Column(Integer, primary_key=True) # Nivel al que se quiere subir (2, 3, 4, 5)
    costo_data = Column(String, nullable=False) # JSON String: '[{"id": "Ore", "qty": 1000}]'