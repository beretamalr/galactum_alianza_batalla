from sqlalchemy.orm import Session
from app.v2_features_beta.models.ship import Ship # type: ignore
from app.models.user import User
from app.v2_features_beta.schemas.ship import ShipStatus, Position # type: ignore
import math
from datetime import datetime, timezone, timedelta # Importamos timezone y timedelta

# Importamos los modelos y schemas que ambas funciones necesitan
from app.v2_features_beta import schemas # type: ignore

def get_all_ships(db: Session):
    ships = db.query(Ship).all()
    result = []
    for ship in ships:
        user = db.query(User).filter(User.id == ship.owner_id).first()
        username = user.username if user else "unknown"
        current_pos = Position(x=ship.current_pos_x, y=ship.current_pos_y)
        start_pos = Position(x=ship.start_pos_x, y=ship.start_pos_y) if ship.start_pos_x is not None and ship.start_pos_y is not None else None
        end_pos = Position(x=ship.end_pos_x, y=ship.end_pos_y) if ship.end_pos_x is not None and ship.end_pos_y is not None else None
        result.append(
            ShipStatus(
                username=username,
                isMoving=ship.is_moving,
                currentPosition=current_pos,
                startPosition=start_pos,
                endPosition=end_pos
            )
        )
    return result

# --- ¡LÓGICA DE MOVIMIENTO! ---
def start_player_move(
    db: Session, 
    user_id: str, # Viene del token JWT
    target_pos: schemas.ship.Position
) -> schemas.ship.ShipMoveResponseData:
    """
    Inicia el movimiento de la nave de un jugador y actualiza la base de datos.
    """
    
    # 1. Encontrar la nave del jugador actual
    ship = db.query(Ship).filter(Ship.owner_id == user_id).first()
    
    if not ship:
        # El endpoint capturará este error y devolverá una respuesta HTTP 404 o 500
        raise Exception("Ship not found for the current user")
        
    # 2. Definir variables de inicio del movimiento
    start_time = datetime.now(timezone.utc)
    start_pos = schemas.ship.Position(x=ship.current_pos_x, y=ship.current_pos_y)
    
    # 3. Calcular distancia y duración del viaje
    # Fórmula de la distancia euclidiana
    distance = math.sqrt(
        (target_pos.x - start_pos.x) ** 2 + 
        (target_pos.y - start_pos.y) ** 2
    )
    
    if distance == 0:
        raise Exception("Already at target position or invalid distance")

    # ¡Usamos la velocidad de la nave desde la base de datos!
    duration_seconds = distance / ship.speed 
    
    # 4. Calcular la hora estimada de llegada (ETA)
    eta = start_time + timedelta(seconds=duration_seconds)

    # 5. ACTUALIZAR todas las columnas de la nave en la BD
    ship.is_moving = True
    ship.start_pos_x = start_pos.x
    ship.start_pos_y = start_pos.y
    ship.end_pos_x = target_pos.x
    ship.end_pos_y = target_pos.y
    ship.movement_start_time = start_time
    ship.estimated_arrival_time = eta
    
    db.commit()   # Guarda los cambios en la base de datos
    db.refresh(ship) # Refresca el objeto 'ship' con los datos guardados

    # 6. Preparar y devolver los datos para la respuesta de la API
    return schemas.ship.ShipMoveResponseData(
        endPosition=target_pos,
        estimatedArrivalTime=eta
    )