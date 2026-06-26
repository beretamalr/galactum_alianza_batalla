# app/api/routes/conflicto.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/conflicto", tags=["Conflictos y Combates"])

@router.get("/activos", status_code=status.HTTP_200_OK, name="Listar Conflictos Activos")
def listar_conflictos(current_user: User = Depends(get_current_user)):
    """
    Retorna las disputas y guerras activas en el servidor para que el jugador
    sepa dónde enviar sus flotas de combate.
    """
    return [
        {
            "id": 501,
            "facción_enemiga": "Piratas del Sindicato Orion",
            "sector": "Cuadrante Delta-9",
            "estado": "En Guerra",
            "peligro": "Alto"
        },
        {
            "id": 502,
            "facción_enemiga": "Corporación Nexus",
            "sector": "Anillos de Ceti Alpha",
            "estado": "Escaramuza",
            "peligro": "Medio"
        }
    ]

@router.post("/atacar", status_code=status.HTTP_200_OK, name="Iniciar Ataque Espacial")
def iniciar_ataque(conflicto_id: int, naves_enviadas: int, current_user: User = Depends(get_current_user)):
    """
    Ordena el despliegue de naves del Comandante actual para atacar un sector en conflicto.
    """
    if naves_enviadas <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes enviar al menos 1 nave de combate a la batalla."
        )
        
    return {
        "status": "combat_initiated",
        "mensaje": f"¡Flota de {current_user.username} en camino!",
        "detalles": {
            "conflicto_id": conflicto_id,
            "fuerza_desplegada": f"{naves_enviadas} Cruceros de Batalla",
            "tiempo_estimado_arribo": "4 minutos"
        }
    }