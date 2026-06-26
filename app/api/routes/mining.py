# app/api/routes/mining.py
from fastapi import APIRouter, Depends, status
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/mining", tags=["Minería (Mining)"])

@router.get("/asteroides", status_code=status.HTTP_200_OK, name="Buscar Asteroides Cercanos")
def listar_asteroides(current_user: User = Depends(get_current_user)):
    """
    Escanea el sector espacial actual en busca de asteroides ricos en minerales.
    """
    return [
        {"id": 901, "nombre": "Asteroide Vesta-X", "recurso": "Titanio", "riqueza": "Alta", "distancia_al": "1.2 LY"},
        {"id": 902, "nombre": "Nube Volátil C-40", "recurso": "Helio-3", "riqueza": "Media", "distancia_al": "0.5 LY"}
    ]

@router.post("/extraer", status_code=status.HTTP_200_OK, name="Enviar Sonda Minera")
def iniciar_mineria(asteroide_id: int, horas: int = 1, current_user: User = Depends(get_current_user)):
    """
    Despliega naves de extracción para recolectar recursos durante un tiempo determinado.
    """
    return {
        "status": "mining_operation_launched",
        "detalles": {
            "asteroide_id": asteroide_id,
            "tiempo_estimado": f"{horas} hora(s)",
            "mensaje": f"Sondas de {current_user.username} extrayendo recursos con éxito."
        }
    }