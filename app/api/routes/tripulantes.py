from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.services import tripulantes_service
from app.schemas.crew import CrewAssignRequest, CrewSpecializeRequest, AcquireCrewRequest

router = APIRouter(
    prefix="/api/v1",
    tags=["crew"],
)

@router.get("/player/crew")
def get_crew(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    
    player_id = current_user.jugador.id
    return tripulantes_service.obtener_tripulantes(db, player_id)

@router.post("/crew/acquire", status_code=status.HTTP_201_CREATED)
def acquire_new_crew(
    request: AcquireCrewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Endpoint para adquirir un nuevo tripulante."""
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    try:
        nuevo_tripulante = tripulantes_service.adquirir_tripulante(db, current_user.jugador.id, request.crew_template_id)
        db.commit()
        db.refresh(nuevo_tripulante)
        return nuevo_tripulante
    except (ValueError, PermissionError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/crew/{crew_id}/assign")
def assign_crew(
    crew_id: int,
    body: CrewAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    
    player_id = current_user.jugador.id
    try:
        resultado = tripulantes_service.asignar_tripulante(db, player_id, crew_id, body.slot_id)
        db.commit()
        return resultado
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/crew/{crew_id}/levelup")
def levelup_crew(
    crew_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Endpoint para mejorar un tripulante existente."""
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    try:
        tripulante_mejorado = tripulantes_service.mejorar_tripulante(db, current_user.jugador.id, crew_id)
        db.commit()
        db.refresh(tripulante_mejorado)
        return {"status": "success", "updated_crew": tripulante_mejorado}
    except (ValueError, PermissionError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/crew/{crew_id}/specialize")
def specialize_crew(
    crew_id: int,
    body: CrewSpecializeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    
    player_id = current_user.jugador.id
    try:
        resultado = tripulantes_service.especializar_tripulante(db, player_id, crew_id, body.specialization_id)
        db.commit()
        return resultado
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
