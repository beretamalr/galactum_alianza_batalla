# app/api/routes/tripulantes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/tripulantes", tags=["Tripulantes"])

@router.get("/mi-nave", status_code=status.HTTP_200_OK, name="Ver Tripulación de la Nave")
def ver_tripulacion(current_user: User = Depends(get_current_user)):
    """
    Retorna la lista de tripulantes trabajando actualmente en las salas de la nave.
    """
    return [
        {"id": 101, "nombre": "Sora Jax", "rol": "Ingeniero de Motores", "eficiencia": "+15%", "estado": "Asignado"},
        {"id": 102, "nombre": "Tariq Vance", "rol": "Oficial de Escudos", "eficiencia": "+10%", "estado": "Asignado"}
    ]

@router.post("/reclutar", status_code=status.HTTP_201_CREATED, name="Reclutar Tripulante")
def reclutar_tripulante(rol_deseado: str, current_user: User = Depends(get_current_user)):
    """
    Contrata un nuevo tripulante para la flota espacial del jugador.
    """
    return {
        "status": "success",
        "message": f"¡Reclutado con éxito un nuevo {rol_deseado} para la nave de {current_user.username}!"
    }