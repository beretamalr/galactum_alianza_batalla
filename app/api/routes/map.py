# app\api\routes\map.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.ship import get_all_ships
from app.schemas.ship import ShipsResponse
from app.services.auth import get_current_user
from app.schemas.asteroid import AsteroidsResponse
from app.services.asteroid_service import get_all_asteroids

router = APIRouter(prefix="/api/v1/map", tags=["map"])

# --- Obtener estado de las naves ---
@router.get("/ships", response_model=ShipsResponse)
def get_ships(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    ships = get_all_ships(db)
    return ShipsResponse(status="success", data=ships)


# --- Obtener información de asteroides ---
@router.get("/asteroids", response_model=AsteroidsResponse)
def get_asteroids(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    asteroids = get_all_asteroids(db)
    return AsteroidsResponse(status="success", data=asteroids)
