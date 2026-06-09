from sqlalchemy.orm import Session
from app.v2_features_beta.models.asteroid import Asteroid # type: ignore
from app.v2_features_beta.schemas.asteroid import AsteroidStatus, Position # type: ignore

def get_all_asteroids(db: Session):
    asteroids = db.query(Asteroid).all()
    result = []
    for ast in asteroids:
        result.append(
            AsteroidStatus(
                asteroidId=ast.asteroid_id,
                position=Position(x=ast.pos_x, y=ast.pos_y),
                resourceType=ast.resource_type
            )
        )
    return result