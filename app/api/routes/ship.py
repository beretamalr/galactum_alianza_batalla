from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.services.auth import get_current_user
from app.services.ship import get_ship_state


router = APIRouter(
    prefix="/ship",
    tags=["Nave"],
)


@router.get(
    "/estado",
    status_code=status.HTTP_200_OK,
    name="Ver Estado de la Nave",
)
def ver_estado_nave(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve la nave persistida del usuario autenticado.

    Si el usuario es antiguo y no tiene nave, el servicio crea una
    automáticamente y la guarda en Neon.
    """
    try:
        return get_ship_state(
            db=db,
            user=current_user,
        )

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible obtener el estado de la nave: " + str(error),
        )