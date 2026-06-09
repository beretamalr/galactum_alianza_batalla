# app/api/routes/misiones.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.services import misiones_service
from app.schemas.misiones import MisionesResponse, MisionReclamarPeticion, MisionReclamarRespuesta

router = APIRouter(prefix="/api/v1/misiones", tags=["Misiones"])

@router.get("/", response_model=MisionesResponse)
def get_misiones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    
    misiones = misiones_service.obtener_misiones(db, current_user.jugador.id)
    return misiones

@router.post("/reclamar", response_model=MisionReclamarRespuesta)
def reclamar_mision(
    peticion: MisionReclamarPeticion,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    try:
        resultado = misiones_service.reclamar_recompensa(db, current_user.jugador.id, peticion.model_dump())
        db.commit()
        return resultado
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))