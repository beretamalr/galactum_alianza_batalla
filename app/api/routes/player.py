from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Any, Dict

from app.services.auth import get_current_user
from app.models.user import User
from app.db.dependencies import get_db
from app.services import ship_rooms_service,ship
from app.services import recursos_service
from app.models.crafting import CatalogoItem
from app.schemas.player import InventoryResponse

# Definimos el router para este módulo
router = APIRouter(prefix="/api/v1/player", tags=["player"])

# --- Obtener perfil del jugador ---
@router.get("/profile", name="Get player profile")
def get_profile(current_user: User = Depends(get_current_user)):
    """
    Devuelve la información básica y los recursos del jugador autenticado.
    """
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado para este usuario.")

    data = {
        "nickname": current_user.jugador.nickname,
        "user_id": current_user.id,
        "player_id": current_user.jugador.id
    }
    return {"status": "success", "data": data}

# --- Obtener configuración de salas de la nave ---
@router.get("/rooms", response_model=List[Dict[str, Any]], name="Get player ship rooms")
def get_ship_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Devuelve una lista con el estado y costo de mejora de todas las salas de la nave.
    """
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado para este usuario.")

    # Llamamos al servicio para obtener las salas desde la BD
    salas = ship_rooms_service.obtener_info_salas(db, player_id=current_user.jugador.id) # type: ignore
    
    return salas

@router.get("/stats", name="Get player final stats")
def get_player_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calcula y devuelve las estadísticas finales de la nave del jugador,
    incluyendo bonificaciones de salas y tripulación.
    """
    try:
        stats = ship.get_player_ship_stats(db, str(current_user.id))
        return {"status": "success", "data": stats}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Obtener inventario de recursos del jugador ---
@router.get("/resources", response_model=InventoryResponse, name="Get player resources")
def get_player_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Devuelve el inventario completo de recursos del jugador autenticado.
    """
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado para este usuario.")

    # Importamos el modelo de inventario aquí para evitar importaciones circulares a nivel de módulo.
    from app.models.inventory import Inventory

    # Realizamos una única consulta con JOIN para obtener todos los datos de una vez.
    # Esto es más eficiente y robusto que hacer múltiples consultas.
    inventario_con_detalles = db.query(
        Inventory.resource_id,
        Inventory.quantity,
        CatalogoItem.nombre,
        CatalogoItem.descripcion,
        CatalogoItem.tipo,
        CatalogoItem.rareza,
        CatalogoItem.imagen_url
    ).join(
        CatalogoItem, Inventory.resource_id == CatalogoItem.id
    ).filter(
        Inventory.player_id == current_user.jugador.id
    ).all()

    # Convertimos la lista de resultados (que son como tuplas) en una lista de diccionarios.
    inventario_enriquecido = [dict(item._mapping) for item in inventario_con_detalles]

    return InventoryResponse(recursos=inventario_enriquecido)

# --- Obtener lista de amigos o aliados ---
@router.get("/friends", name="Get player friends")
def get_friends(current_user: User = Depends(get_current_user)):
    """
    Devuelve la lista de amigos o aliados del jugador.
    """
    data = [
        {"username": "aliado_1", "status": "online"},
        {"username": "aliado_2", "status": "offline"},
    ]
    return {"status": "success", "data": data}


# --- Actualizar configuración del jugador ---
@router.put("/settings", name="Update player settings")
def update_settings(
    settings: dict, current_user: User = Depends(get_current_user)
):
    """
    Actualiza la configuración del jugador (mock).
    """
    # Por ahora solo devolvemos lo que llega
    return {"status": "success", "updated_settings": settings}
