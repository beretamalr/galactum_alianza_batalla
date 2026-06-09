# app\schemas\asteroid.py
from pydantic import BaseModel

class Position(BaseModel):
    x: float
    y: float

class AsteroidStatus(BaseModel):
    asteroid: str
    position: Position
    resource_id: int
    resource_name: str
    cantidad_restante: int
    cantidad_maxima: int
    


class AsteroidsResponse(BaseModel):
    status: str = "success"
    data: list[AsteroidStatus]