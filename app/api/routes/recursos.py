# app/api/routes/recursos.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# --- Importaciones del proyecto ---
from app.db.dependencies import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.services import recursos_service
from app.schemas.recursos import ResourceAdd, RecipeConvert, ResourceConvertResponse
from app.schemas.player import InventoryItem

router = APIRouter(
    prefix="/api/v1",
    tags=["Recursos"]
)

@router.post("/resources", response_model=List[InventoryItem], status_code=status.HTTP_200_OK)
def add_resources(
    peticion: ResourceAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Añade una cantidad de un recurso específico al inventario del jugador.
    Simula la minería o la recolección de recursos.
    """
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado para este usuario.")

    try:
        # El servicio espera una lista de diccionarios
        lista_recursos = [{"id": peticion.resource_id, "quantity": peticion.quantity}]
        recursos_service.agregar_recursos_jugador(db, player_id=current_user.jugador.id, lista_recursos=lista_recursos)
        db.commit()
        # Devolvemos el inventario completo y actualizado
        return recursos_service.obtener_inventario_jugador(db, player_id=current_user.jugador.id)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al añadir recursos: {e}")

@router.post("/resources/convert", response_model=ResourceConvertResponse, status_code=status.HTTP_200_OK)
def convert_resources(
    peticion: RecipeConvert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Convierte un conjunto de recursos en otro según una receta definida.
    Toda la operación es transaccional.
    """
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado para este usuario.")

    try:
        resultado = recursos_service.convertir_recursos(
            db,
            player_id=current_user.jugador.id,
            recipe_id=peticion.recipe_id
        )
        db.commit()
        return resultado
    except Exception as e:
        db.rollback()
        if "Receta no encontrada" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        if "Recursos insuficientes" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al convertir recursos.")