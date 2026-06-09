# En app/api/routes/ship.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.schemas.ship import ShipMoveRequest, ShipMoveResponse
# --- ¡IMPORTACIÓN CORREGIDA! ---
# Apuntamos a los nuevos servicios en la carpeta de servicios
from app.services import ship
from app.services import ship_rooms_service # Importamos el servicio de salas
from typing import List, Dict, Any # Para el tipado de la respuesta

router = APIRouter(prefix="/api/v1/player", tags=["player"])

@router.post(
    "/move", 
    response_model=ShipMoveResponse, # Usamos el schema importado
    summary="Iniciar Movimiento de la Nave"
)
async def move_ship(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), # Usamos el modelo importado
    move_request: ShipMoveRequest # Usamos el schema importado
):
    """
    Establece un nuevo punto de destino para la nave del jugador.
    """
    try:
        # 1. Llamamos a la función del nuevo servicio
        # Le pasamos la BD, el ID del usuario y la posición objetivo
        real_data = ship.start_player_move(
            db=db,
            user_id=str(current_user.id),
            target_pos=move_request.targetPosition
        )
        
        return {
            "status": "success",
            "message": "Movement initiated.",
            "data": real_data # Usamos los datos reales devueltos por el servicio
        }
        
    except Exception as e:
        # 2. Si el servicio falla, capturamos la excepción y devolvemos un error HTTP.
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

# ===================================================================
# 🔹 Tarea 2.1: Endpoints de Gestión de Salas
# ===================================================================

@router.get(
    "/rooms",
    # Definimos que la respuesta será una lista que contiene diccionarios.
    # Esto le da a FastAPI una idea de la estructura de la respuesta.
    response_model=List[Dict[str, Any]],
    summary="Obtener Información de las Salas de la Nave"
)
async def get_player_rooms(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Devuelve la lista de salas del jugador, su nivel actual y el costo de la próxima mejora.
    """
    # Llamamos a la nueva función del servicio que obtiene la información combinada.
    # El ID del jugador se obtiene a través del token de autenticación.
    rooms_info = ship_rooms_service.obtener_info_salas(db=db, player_id=current_user.jugador.id)
    return rooms_info


@router.post(
    "/room/{room_id}/upgrade",
    summary="Mejorar una Sala de la Nave"
)
async def upgrade_player_room(
    room_id: str, # El ID de la sala se obtiene del path de la URL.
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Inicia el proceso de mejora para una sala específica.
    Consume los recursos necesarios si están disponibles.
    """
    try:
        # La lógica transaccional está encapsulada en el servicio.
        # El servicio ahora inicia una mejora asíncrona.
        resultado = ship_rooms_service.upgrade_room(db=db, player_id=current_user.jugador.id, room_id=room_id) # type: ignore
        db.commit() # Si el servicio no lanzó una excepción, confirmamos la transacción.
        
        return resultado
    
    except Exception as e:
        db.rollback() # Si algo falla (ej. falta de recursos), revertimos cualquier cambio.
        # Devolvemos un error 400 (Bad Request) con el mensaje de la excepción.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
