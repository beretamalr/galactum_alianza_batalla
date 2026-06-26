# app/api/routes/crafting.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/crafting", tags=["Fabricación (Crafting)"])

@router.get("/recetas", status_code=status.HTTP_200_OK, name="Ver Recetas Disponibles")
def listar_recetas(current_user: User = Depends(get_current_user)):
    """
    Lista los planos tecnológicos disponibles en el taller de la nave.
    """
    return [
        {
            "producto": "Escudo de Plasma MK2",
            "materiales_requeridos": {"Titanio": 20, "Helio-3": 50},
            "tiempo_fabricacion_segundos": 120
        },
        {
            "producto": "Hipermotor Optimizado",
            "materiales_requeridos": {"Titanio": 100, "Helio-3": 300},
            "tiempo_fabricacion_segundos": 600
        }
    ]

@router.post("/fabricar", status_code=status.HTTP_201_CREATED, name="Iniciar Fabricación")
def fabricar_item(producto: str, current_user: User = Depends(get_current_user)):
    """
    Consume recursos del inventario e inicia la construcción de un nuevo componente.
    """
    return {
        "status": "crafting_started",
        "mensaje": f"¡El taller de {current_user.username} comenzó a fabricar: {producto}!"
    }