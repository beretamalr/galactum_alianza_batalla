# app/models/config_unit_recipes.py
from sqlalchemy import Column, String
from app.db.base import Base

class ConfigUnitRecipe(Base):
    __tablename__ = "config_unit_recipes"

    unit_id = Column(String, primary_key=True, index=True) # Ej: "Infanteria"
    resource_cost_json = Column(String, nullable=False) # JSON String: '[{"id": "Ore", "quantity": 25}]'