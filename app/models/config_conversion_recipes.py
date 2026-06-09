# app/models/config_conversion_recipes.py
from sqlalchemy import Column, String
from app.db.base import Base

class ConfigConversionRecipe(Base):
    __tablename__ = "config_conversion_recipes"

    recipe_id = Column(String, primary_key=True, index=True)
    cost_json = Column(String, nullable=False) # JSON String: '[{"id": "Roderitium", "quantity": 10}]'
    product_json = Column(String, nullable=False) # JSON String: '[{"id": "Ore", "quantity": 1}]'