# app/api/routes/ship.py
from fastapi import APIRouter, Depends, status
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ship", tags=["Nave"])

@router.get("/estado", status_code=status.HTTP_200_OK, name="Ver Estado de la Nave")
def ver_estado_nave(current_user: User = Depends(get_current_user)):
    """
    Retorna los componentes críticos y estadísticas de la nave del comandante.
    """
    return {
        "comandante": current_user.username,
        "nave": {
            "nombre": "Galactum Explorer",
            "nivel_casco": 1,
            "escudos_max": 100,
            "energia_actual": 50,
            "energia_max": 50,
            "mejoras_disponibles": True
        }
  }