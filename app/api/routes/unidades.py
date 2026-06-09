# app/api/routes/unidades.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.services import unidades_service
from app.schemas.unidades import UnitCreateRequest, UnitCreateResponse

router = APIRouter(prefix="/api/v1/create", tags=["Unidades"])

@router.post("/unit", response_model=UnitCreateResponse)
def create_unit_endpoint(
    peticion: UnitCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea una o más unidades de un tipo específico, consumiendo los recursos necesarios.
    """
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    try:
        resultado = unidades_service.create_unit(
            db, current_user.jugador.id, peticion.unit_type_id, peticion.quantity
        )
        db.commit()
        return UnitCreateResponse(status="success", message=f"Creado {resultado['created_quantity']}x {resultado['unit_type_id']}", **resultado)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))