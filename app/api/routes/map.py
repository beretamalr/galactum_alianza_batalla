# app/api/routes/map.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/map", tags=["Mapa y Exploración"])

@router.get("/sectores", status_code=status.HTTP_200_OK, name="Obtener Mapa Estelar")
def obtener_mapa(current_user: User = Depends(get_current_user)):
    """
    Descarga los puntos de interés del cuadrante para que Godot dibuje el mapa.
    """
    return [
        {"id": 1, "nombre": "Planeta Nova Prime", "tipo": "Habitable", "x": 14.5, "y": -22.3},
        {"id": 2, "nombre": "Estación Comercial Omega", "tipo": "Estación", "x": 0.0, "y": 5.8},
        {"id": 3, "nombre": "Agujero de Gusano 'Abismo'", "tipo": "Anomalía", "x": -45.1, "y": 88.2}
    ]

@router.post("/viajar", status_code=status.HTTP_200_OK, name="Saltar de Cuadrante")
def viajar_a_sector(sector_id: int, current_user: User = Depends(get_current_user)):
    """
    Consume combustible del motor e inicia el viaje hiperespacial al sector seleccionado.
    """
    return {
        "status": "hyperjump_successful",
        "mensaje": f"¡La nave de {current_user.username} saltó con éxito al sector {sector_id}!",
        "combustible_consumido": 25,
        "coordenadas_actuales": {"x": 14.5, "y": -22.3}
    }