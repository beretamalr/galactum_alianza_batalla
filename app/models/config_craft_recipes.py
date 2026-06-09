# app/models/config_craft_recipes.py
from sqlalchemy import Column, Integer, String
from app.db.base import Base

class ConfigCraftRecipe(Base):
    __tablename__ = "config_craft_recipes"

    recipe_id = Column(String, primary_key=True, index=True)
    output_item_id = Column(String, nullable=False)
    required_room_id = Column(String, nullable=False)
    required_room_level = Column(Integer, nullable=False)
    resource_cost_json = Column(String, nullable=False) # JSON String: '[{"id": "Ore", "quantity": 50}]'