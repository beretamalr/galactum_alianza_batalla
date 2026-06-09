import uuid
from sqlalchemy.orm import Session, joinedload
from app.models.ship import Ship
from app.models.ship_rooms import ShipRoom
from app.models.tripulante import Tripulante
from app.models.user import User
from app.schemas.ship import ShipStatus, Position, ShipMoveResponseData
import math
import random
from datetime import datetime, timezone, timedelta
from typing import cast, Optional

# Límites del mapa
MAP_MIN_COORDINATE = -10000
MAP_MAX_COORDINATE = 10000

def get_all_ships(db: Session):
    """
    Obtiene el estado de todas las naves para el mapa.
    """
    ships = db.query(Ship).options(
        joinedload(Ship.owner).joinedload(User.jugador)
    ).all()

    result = []
    for ship in ships:
        nickname = "unknown"
        if ship.owner and ship.owner.jugador:
            nickname = ship.owner.jugador.nickname

        # Castings para evitar errores de linter
        c_pos_x = cast(float, ship.current_pos_x)
        c_pos_y = cast(float, ship.current_pos_y)
        
        current_pos = Position(x=c_pos_x, y=c_pos_y)
        
        # Validación segura de start_pos
        start_pos = None
        if ship.start_pos_x is not None and ship.start_pos_y is not None:
            start_pos = Position(
                x=cast(float, ship.start_pos_x), 
                y=cast(float, ship.start_pos_y)
            )

        # Validación segura de end_pos
        end_pos = None
        if ship.end_pos_x is not None and ship.end_pos_y is not None:
            end_pos = Position(
                x=cast(float, ship.end_pos_x), 
                y=cast(float, ship.end_pos_y)
            )

        result.append(
            ShipStatus(
                username=nickname,
                isMoving=cast(bool, ship.is_moving),
                currentPosition=current_pos,
                startPosition=start_pos,
                endPosition=end_pos,
                movementStartTime=cast(Optional[datetime], ship.movement_start_time),
                estimatedArrivalTime=cast(Optional[datetime], ship.estimated_arrival_time)
            )
        )
    return result

def start_player_move(
    db: Session, 
    user_id: str,
    target_pos: Position
) -> ShipMoveResponseData:
    """
    Inicia el movimiento de la nave y corrige la posición inicial.
    Usa 'cast' explícito para satisfacer al linter (Pylance).
    """
    
    # 0. Limitar coordenadas (Clamp)
    clamped_x = max(MAP_MIN_COORDINATE, min(target_pos.x, MAP_MAX_COORDINATE))
    clamped_y = max(MAP_MIN_COORDINATE, min(target_pos.y, MAP_MAX_COORDINATE))
    
    clamped_target_pos = Position(x=clamped_x, y=clamped_y)

    # 1. Encontrar la nave
    ship = db.query(Ship).filter(Ship.owner_id == user_id).first()
    
    if not ship:
        raise Exception("Ship not found for the current user")
    
    # --- CORRECCIÓN DE POSICIÓN PREVIA (Linter Friendly) ---
    now = datetime.now(timezone.utc)

    # 1. Extraemos y casteamos las variables primero.
    mov_start = cast(Optional[datetime], ship.movement_start_time)
    est_arrival = cast(Optional[datetime], ship.estimated_arrival_time)
    start_x = cast(Optional[float], ship.start_pos_x)
    end_x = cast(Optional[float], ship.end_pos_x)
    start_y = cast(Optional[float], ship.start_pos_y)
    end_y = cast(Optional[float], ship.end_pos_y)
    is_moving = cast(bool, ship.is_moving)

    # Ahora el IF usa variables tipadas correctamente
    if mov_start and est_arrival and start_x is not None and end_x is not None:
        
        # --- FIX: Normalizar zonas horarias ---
        if est_arrival.tzinfo is None:
            est_arrival = est_arrival.replace(tzinfo=timezone.utc)

        if mov_start.tzinfo is None:
            mov_start = mov_start.replace(tzinfo=timezone.utc)
        # --------------------------------------

        # CASO 1: Viaje anterior finalizado
        if now >= est_arrival:
            # Agregamos # type: ignore para calmar a Pylance
            ship.current_pos_x = end_x  # type: ignore
            ship.current_pos_y = end_y  # type: ignore
            ship.is_moving = False      # type: ignore
        
        # CASO 2: Cambio de rumbo en vuelo
        elif is_moving:
            total_duration = (est_arrival - mov_start).total_seconds()
            elapsed_time = (now - mov_start).total_seconds()
            
            s_y = cast(float, start_y)
            e_y = cast(float, end_y)

            if total_duration > 0:
                progress = elapsed_time / total_duration
                current_x = start_x + (end_x - start_x) * progress
                current_y = s_y + (e_y - s_y) * progress
                
                # Agregamos # type: ignore aquí también
                ship.current_pos_x = current_x  # type: ignore
                ship.current_pos_y = current_y  # type: ignore
    
    # -------------------------------------

    # 2. Definir nuevo viaje
    start_time = now
    
    # Usamos la posición actual corregida (y casteada) como punto de partida
    current_x_val = cast(float, ship.current_pos_x)
    current_y_val = cast(float, ship.current_pos_y)
    
    start_pos = Position(x=current_x_val, y=current_y_val)
    
    # 3. Calcular distancia
    distance = math.sqrt(
        (clamped_target_pos.x - start_pos.x) ** 2 + 
        (clamped_target_pos.y - start_pos.y) ** 2
    )
    
    if distance == 0:
        pass 

    # Evitar división por cero en speed
    speed_val = cast(Optional[float], ship.speed)
    speed = float(speed_val) if speed_val and speed_val > 0 else 1.0
    
    duration_seconds = distance / speed
    
    # 4. Calcular ETA
    eta = start_time + timedelta(seconds=duration_seconds)

    # 5. Guardar en BD (Estas líneas ya tenían el ignore y funcionaban bien)
    ship.is_moving = True  # type: ignore
    ship.start_pos_x = start_pos.x  # type: ignore
    ship.start_pos_y = start_pos.y  # type: ignore
    ship.end_pos_x = clamped_target_pos.x  # type: ignore
    ship.end_pos_y = clamped_target_pos.y  # type: ignore
    ship.movement_start_time = start_time  # type: ignore
    ship.estimated_arrival_time = eta  # type: ignore

    db.commit()
    db.refresh(ship)

    # 6. Retorno de datos
    return ShipMoveResponseData(
        startPosition=start_pos,
        endPosition=clamped_target_pos,
        movementStartTime=start_time,
        estimatedArrivalTime=eta
    )

def get_player_ship_stats(db: Session, user_id: str):
    """
    Calcula estadísticas finales de la nave.
    """
    ship = db.query(Ship).filter(Ship.owner_id == user_id).first()
    if not ship:
        raise Exception("Nave no encontrada")

    player_id = ship.owner.jugador.id # type: ignore
    rooms = db.query(ShipRoom).filter(ShipRoom.player_id == player_id).all()
    crew = db.query(Tripulante).filter(Tripulante.player_id == player_id).all()

    final_stats = {
        "cargo_capacity": ship.cargo_capacity,
        "shield_points": ship.shield_points,
        "hull_points": ship.hull_points,
        "impulse_speed": ship.speed,
        "extractor_level": ship.extractor_level,
        "weapon_slots": ship.weapon_slots,
        "crew_slots": ship.crew_slots
    }

    for room in rooms:
        if cast(str, room.room_id) == "Fabrica":
            final_stats["cargo_capacity"] += cast(int, room.level) * 100

    for member in crew:
        if cast(int, member.slot_id) == 1: 
            final_stats["impulse_speed"] += cast(int, member.agilidad) * 5
        
        if cast(int, member.slot_id) == 2:
            final_stats["extractor_level"] += cast(int, member.percepcion) // 10

    return final_stats

def create_initial_ship(db: Session, user_id: uuid.UUID) -> Ship:
    """
    Crea nave inicial.
    """
    initial_pos_x = float(random.randint(MAP_MIN_COORDINATE, MAP_MAX_COORDINATE))
    initial_pos_y = float(random.randint(MAP_MIN_COORDINATE, MAP_MAX_COORDINATE))

    new_ship = Ship(
        owner_id=user_id,
        is_moving=False,
        current_pos_x=initial_pos_x,
        current_pos_y=initial_pos_y,
        start_pos_x=initial_pos_x,
        start_pos_y=initial_pos_y,
    )

    db.add(new_ship)
    return new_ship