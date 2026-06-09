# app/api/routes/config.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.services import ship_rooms_service
from app.schemas.ship import RoomUpgradeRequest, RoomUpgradeResponse

router = APIRouter(prefix="/api/v1/config", tags=["Configuración"])

@router.post("/upgrade_room", response_model=RoomUpgradeResponse)
def upgrade_room_endpoint(
    peticion: RoomUpgradeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mejora una sala de la nave del jugador, consumiendo los recursos necesarios.
    """
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    try:
        sala_actualizada = ship_rooms_service.upgrade_room(db, current_user.jugador.id, peticion.room_id)
        db.commit()
        return RoomUpgradeResponse(status="success", message=f"Sala {sala_actualizada.room_id} mejorada a nivel {sala_actualizada.level}", room_id=sala_actualizada.room_id, new_level=sala_actualizada.level) # type: ignore
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))