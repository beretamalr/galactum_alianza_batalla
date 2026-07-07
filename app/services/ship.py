import math
import random
import uuid

from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from sqlalchemy.orm import Session, joinedload

from app.models.jugador import Jugador
from app.models.ship import Ship
from app.models.ship_rooms import ShipRoom
from app.models.tripulante import Tripulante
from app.models.user import User

from app.schemas.ship import (
    Position,
    ShipMoveResponseData,
    ShipStatus,
)


MAP_MIN_COORDINATE = -10000
MAP_MAX_COORDINATE = 10000


def _to_float(value, default: float = 0.0) -> float:
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default: int = 0) -> int:
    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_aware_datetime(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value


def _normalize_user_id(user_id: Union[str, uuid.UUID]) -> uuid.UUID:
    if isinstance(user_id, uuid.UUID):
        return user_id

    return uuid.UUID(str(user_id))


def _sync_ship_position(
    ship: Ship,
    now: Optional[datetime] = None,
) -> bool:
    """
    Actualiza posición si el viaje terminó o calcula la posición
    intermedia cuando la nave se encuentra viajando.

    Retorna True si modificó la nave.
    """

    if not ship.is_moving:
        return False

    now = now or datetime.now(timezone.utc)

    start_time = _to_aware_datetime(ship.movement_start_time)
    arrival_time = _to_aware_datetime(ship.estimated_arrival_time)

    if (
        start_time is None
        or arrival_time is None
        or ship.start_pos_x is None
        or ship.start_pos_y is None
        or ship.end_pos_x is None
        or ship.end_pos_y is None
    ):
        return False

    start_x = _to_float(ship.start_pos_x)
    start_y = _to_float(ship.start_pos_y)
    end_x = _to_float(ship.end_pos_x)
    end_y = _to_float(ship.end_pos_y)

    if now >= arrival_time:
        ship.current_pos_x = end_x
        ship.current_pos_y = end_y
        ship.is_moving = False

        ship.start_pos_x = None
        ship.start_pos_y = None
        ship.end_pos_x = None
        ship.end_pos_y = None
        ship.movement_start_time = None
        ship.estimated_arrival_time = None

        return True

    total_seconds = (arrival_time - start_time).total_seconds()

    if total_seconds <= 0:
        return False

    elapsed_seconds = (now - start_time).total_seconds()

    progress = max(0.0, min(elapsed_seconds / total_seconds, 1.0))

    ship.current_pos_x = start_x + ((end_x - start_x) * progress)
    ship.current_pos_y = start_y + ((end_y - start_y) * progress)

    return True


def create_initial_ship(
    db: Session,
    user_id: uuid.UUID,
    ship_name: Optional[str] = None,
) -> Ship:
    """
    Crea la nave inicial de un usuario nuevo.

    La función valida antes si el usuario ya tiene una nave para
    evitar duplicaciones durante un registro repetido.
    """

    existing_ship = (
        db.query(Ship)
        .filter(Ship.owner_id == user_id)
        .first()
    )

    if existing_ship is not None:
        return existing_ship

    initial_pos_x = float(
        random.randint(
            MAP_MIN_COORDINATE,
            MAP_MAX_COORDINATE,
        )
    )

    initial_pos_y = float(
        random.randint(
            MAP_MIN_COORDINATE,
            MAP_MAX_COORDINATE,
        )
    )

    new_ship = Ship(
        owner_id=user_id,
        name=ship_name or "Ares Explorer",
        level=1,

        energy_current=100,
        energy_max=100,

        shield_current=100,
        shield_max=100,

        hull_current=500,
        hull_max=500,

        cargo_capacity=1000,
        extractor_level=1,
        weapon_slots=2,
        crew_slots=4,

        is_moving=False,

        current_pos_x=initial_pos_x,
        current_pos_y=initial_pos_y,

        start_pos_x=initial_pos_x,
        start_pos_y=initial_pos_y,

        speed=100.0,
    )

    db.add(new_ship)
    db.flush()

    return new_ship


def get_or_create_ship(
    db: Session,
    user: User,
) -> Ship:
    """
    Obtiene la nave de un usuario.

    Usuarios registrados antes de esta mejora pueden no tener nave.
    En ese caso se crea una automáticamente y queda persistida.
    """

    ship = (
        db.query(Ship)
        .filter(Ship.owner_id == user.id)
        .first()
    )

    if ship is not None:
        return ship

    ship = create_initial_ship(
        db=db,
        user_id=user.id,
        ship_name=f"Nave de {user.username}",
    )

    db.commit()
    db.refresh(ship)

    return ship


def get_ship_state(
    db: Session,
    user: User,
) -> dict:
    """
    Construye el contrato JSON para GET /ship/estado.
    """

    ship = get_or_create_ship(db, user)

    position_changed = _sync_ship_position(ship)

    if position_changed:
        db.commit()
        db.refresh(ship)

    return {
        "comandante": user.username,
        "nave": {
            "id": ship.id,
            "nombre": ship.name,
            "nivel": _to_int(ship.level, 1),

            "energia_actual": _to_int(ship.energy_current, 100),
            "energia_maxima": _to_int(ship.energy_max, 100),

            "escudo_actual": _to_int(ship.shield_current, 100),
            "escudo_maximo": _to_int(ship.shield_max, 100),

            "casco_actual": _to_int(ship.hull_current, 500),
            "casco_maximo": _to_int(ship.hull_max, 500),

            "capacidad_carga": _to_int(ship.cargo_capacity, 1000),
            "nivel_extractor": _to_int(ship.extractor_level, 1),
            "espacios_armas": _to_int(ship.weapon_slots, 2),
            "espacios_tripulacion": _to_int(ship.crew_slots, 4),

            "posicion": {
                "x": _to_float(ship.current_pos_x),
                "y": _to_float(ship.current_pos_y),
            },

            "en_movimiento": bool(ship.is_moving),
            "velocidad": _to_float(ship.speed, 100.0),
        },
    }


def get_all_ships(db: Session):
    """
    Obtiene las naves existentes para dibujarlas en el mapa.
    """

    ships = (
        db.query(Ship)
        .options(
            joinedload(Ship.owner).joinedload(User.jugador)
        )
        .all()
    )

    modified = False
    result = []

    for ship in ships:
        if _sync_ship_position(ship):
            modified = True

        nickname = "Comandante desconocido"

        if ship.owner is not None and ship.owner.jugador is not None:
            nickname = ship.owner.jugador.nickname

        start_position = None
        end_position = None

        if (
            ship.start_pos_x is not None
            and ship.start_pos_y is not None
        ):
            start_position = Position(
                x=_to_float(ship.start_pos_x),
                y=_to_float(ship.start_pos_y),
            )

        if (
            ship.end_pos_x is not None
            and ship.end_pos_y is not None
        ):
            end_position = Position(
                x=_to_float(ship.end_pos_x),
                y=_to_float(ship.end_pos_y),
            )

        result.append(
            ShipStatus(
                username=nickname,
                isMoving=bool(ship.is_moving),

                currentPosition=Position(
                    x=_to_float(ship.current_pos_x),
                    y=_to_float(ship.current_pos_y),
                ),

                startPosition=start_position,
                endPosition=end_position,

                movementStartTime=ship.movement_start_time,
                estimatedArrivalTime=ship.estimated_arrival_time,
            )
        )

    if modified:
        db.commit()

    return result


def start_player_move(
    db: Session,
    user_id: Union[str, uuid.UUID],
    target_pos: Position,
) -> ShipMoveResponseData:
    """
    Inicia o redirige el viaje de una nave.
    """

    normalized_user_id = _normalize_user_id(user_id)

    ship = (
        db.query(Ship)
        .filter(Ship.owner_id == normalized_user_id)
        .first()
    )

    if ship is None:
        raise ValueError(
            "No se encontró una nave para el usuario actual."
        )

    _sync_ship_position(ship)

    clamped_x = max(
        MAP_MIN_COORDINATE,
        min(target_pos.x, MAP_MAX_COORDINATE),
    )

    clamped_y = max(
        MAP_MIN_COORDINATE,
        min(target_pos.y, MAP_MAX_COORDINATE),
    )

    start_position = Position(
        x=_to_float(ship.current_pos_x),
        y=_to_float(ship.current_pos_y),
    )

    end_position = Position(
        x=clamped_x,
        y=clamped_y,
    )

    distance = math.sqrt(
        ((end_position.x - start_position.x) ** 2)
        + ((end_position.y - start_position.y) ** 2)
    )

    speed = max(
        _to_float(ship.speed, 100.0),
        1.0,
    )

    duration_seconds = distance / speed

    movement_start = datetime.now(timezone.utc)
    estimated_arrival = movement_start + timedelta(
        seconds=duration_seconds
    )

    ship.is_moving = True

    ship.start_pos_x = start_position.x
    ship.start_pos_y = start_position.y

    ship.end_pos_x = end_position.x
    ship.end_pos_y = end_position.y

    ship.movement_start_time = movement_start
    ship.estimated_arrival_time = estimated_arrival

    db.commit()
    db.refresh(ship)

    return ShipMoveResponseData(
        startPosition=start_position,
        endPosition=end_position,
        movementStartTime=movement_start,
        estimatedArrivalTime=estimated_arrival,
    )


def get_player_ship_stats(
    db: Session,
    user_id: Union[str, uuid.UUID],
) -> dict:
    """
    Retorna estadísticas de nave para el endpoint de jugador.

    Mantiene compatibilidad con /player/stats, evitando depender
    de atributos comentados o inexistentes del modelo anterior.
    """

    normalized_user_id = _normalize_user_id(user_id)

    ship = (
        db.query(Ship)
        .filter(Ship.owner_id == normalized_user_id)
        .first()
    )

    if ship is None:
        raise ValueError("Nave no encontrada.")

    player = (
        db.query(Jugador)
        .filter(Jugador.user_id == normalized_user_id)
        .first()
    )

    if player is None:
        raise ValueError(
            "Jugador no encontrado para la nave actual."
        )

    rooms = (
        db.query(ShipRoom)
        .filter(ShipRoom.player_id == player.id)
        .all()
    )

    crew_count = (
        db.query(Tripulante)
        .filter(Tripulante.player_id == player.id)
        .count()
    )

    cargo_capacity = _to_int(ship.cargo_capacity, 1000)
    weapon_slots = _to_int(ship.weapon_slots, 2)

    for room in rooms:
        room_id = str(room.room_id).lower()
        room_level = _to_int(room.level, 1)

        if room_id == "fabrica":
            cargo_capacity += room_level * 100

        if room_id == "armeria":
            weapon_slots += room_level

    return {
        "cargo_capacity": cargo_capacity,

        "shield_points": _to_int(
            ship.shield_current,
            100,
        ),

        "hull_points": _to_int(
            ship.hull_current,
            500,
        ),

        "impulse_speed": _to_float(
            ship.speed,
            100.0,
        ),

        "extractor_level": _to_int(
            ship.extractor_level,
            1,
        ),

        "weapon_slots": weapon_slots,

        "crew_slots": _to_int(
            ship.crew_slots,
            4,
        ),

        "crew_assigned": crew_count,
    }