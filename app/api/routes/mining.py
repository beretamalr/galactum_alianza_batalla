# app/api/routes/mining.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.services import mining_service
from app.schemas.mining import MiningStartRequest, MiningInfoResponse, MiningClaimResponse

# Se agrupan las rutas bajo el prefijo /mining
router = APIRouter(prefix="/api/v1/mining", tags=["Mining"])

@router.post("/iniciar", response_model=MiningInfoResponse, status_code=status.HTTP_200_OK, response_model_by_alias=True)
def iniciar_minado(
    request: MiningStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Inicia el proceso de minado en un asteroide, bloqueándolo para el usuario.
    Devuelve la información sobre el tiempo de finalización.
    """
    mining_info = mining_service.start_mining(
        db=db,
        user=current_user,
        asteroid_name=request.asteroid_name
    )
    return mining_info

@router.post("/reclamar", response_model=MiningClaimResponse, status_code=status.HTTP_200_OK, response_model_by_alias=True)
def reclamar_minado(
    request: MiningStartRequest, # Se reutiliza el request para obtener el asteroid_name
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reclama los recursos una vez que el tiempo de minado ha concluido.
    Verifica que el tiempo se haya cumplido y que el reclamante sea el minero original.
    """
    claim_response = mining_service.confirma_mining(
        db=db,
        user=current_user,
        asteroid_name=request.asteroid_name
    )
    return claim_response
