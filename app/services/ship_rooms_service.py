import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import cast
from sqlalchemy.orm import Session

# Importaciones de Modelos
from app.models.ship_rooms import ShipRoom
from app.models.user import User
from app.models.config_room_costs import ConfigRoomCost

# IMPORTACIONES DIRECTAS: Evitan el error de dependencia circular en app.services
from app.services.recursos_service import verificar_y_consumir_recursos
from app.services.misiones_service import actualizar_progreso_mision

# Lista de salas iniciales
SALAS_INICIALES = [
    {"room_id": "Fabrica", "level": 1},
    {"room_id": "Armeria", "level": 1}
]

# Mock de datos estáticos para las salas.
CONFIG_ROOM_DETAILS = {
    "Fabrica": {"name": "Fábrica", "description": "Produce unidades y equipamiento básico."},
    "Armeria": {"name": "Armería", "description": "Diseña y construye armamento avanzado."}
}

def crear_salas_iniciales(db: Session, user_id: uuid.UUID):
    """
    Crea las salas iniciales para un jugador al registrarse.
    Recibe user_id (UUID) y busca el jugador correspondiente en la sesión local.
    """
    # 🟢 MEJORA: Buscamos primero en el mapa de identidad local de SQLAlchemy
    user = db.get(User, user_id)
    if not user:
        raise Exception("No se encontró la instancia del usuario en el sistema.")

    # Obtenemos la referencia del jugador asignado en la transacción
    player = user.jugador
    
    # 🟢 PLAN DE RESPALDO: Si la relación asíncrona de SQLAlchemy no se ha poblado, buscamos por ID
    if not player:
        from app.models.jugador import Jugador
        player = db.query(Jugador).filter(Jugador.user_id == user_id).first()

    if not player:
        raise Exception("No se encontró el perfil de jugador para el usuario al crear salas.")

    player_id = player.id 
    for sala in SALAS_INICIALES:
        db_room = ShipRoom(
            player_id=player_id,
            room_id=sala["room_id"],
            level=sala["level"]
        )
        db.add(db_room)

def obtener_info_salas(db: Session, player_id: int):
    """
    Obtiene la información de las salas de un jugador, incluyendo el costo de la próxima mejora.
    """
    player_rooms = db.query(ShipRoom).filter(ShipRoom.player_id == player_id).all()
 
    response_data = []
    for room in player_rooms:
        next_level = room.level + 1
        
        cost_config = db.query(ConfigRoomCost).filter(
            ConfigRoomCost.room_id == room.room_id,
            ConfigRoomCost.target_level == next_level
        ).first()
        
        room_info = {
            "room_id": room.room_id,
            "name": CONFIG_ROOM_DETAILS.get(cast(str, room.room_id), {}).get("name", room.room_id),
            "level": room.level,
            "status": room.status, 
            "next_level_desc": f"Mejora la eficiencia y desbloquea nuevas recetas de nivel {next_level}." if cost_config else "Nivel máximo alcanzado.",
            "upgrade_cost": json.loads(cost_config.cost_data) if cost_config else [], # type: ignore
            "completion_time": room.upgrade_finish_time 
        }
        response_data.append(room_info)
        
    return response_data

def upgrade_room(db: Session, player_id: int, room_id: str):
    """
    Lógica de negocio para INICIAR la mejora asíncrona de una sala.
    """
    room_to_upgrade = db.query(ShipRoom).filter(
        ShipRoom.player_id == player_id,
        ShipRoom.room_id == room_id
    ).with_for_update().first()

    if not room_to_upgrade:
        raise Exception(f"Sala '{room_id}' no encontrada para este jugador.")

    if room_to_upgrade.status == 'Upgrading': 
        raise Exception(f"La sala '{room_id}' ya se está mejorando.")

    current_level = room_to_upgrade.level
    target_level = current_level + 1

    cost_config = db.query(ConfigRoomCost).filter(
        ConfigRoomCost.room_id == room_id,
        ConfigRoomCost.target_level == target_level
    ).first()

    if not cost_config:
        raise Exception(f"No hay un costo de mejora definido para '{room_id}' a nivel {target_level}.")

    costo_lista = json.loads(cost_config.cost_data) # type: ignore
    duration_seconds = cost_config.duration_seconds if hasattr(cost_config, 'duration_seconds') else 3600 

    # Llamada directa a la función importada
    verificar_y_consumir_recursos(db, player_id, costo_lista) # type: ignore

    now = datetime.now(timezone.utc)
    completion_time = now + timedelta(seconds=duration_seconds)
    
    room_to_upgrade.status = 'Upgrading' # type: ignore
    room_to_upgrade.upgrade_finish_time = completion_time # type: ignore

    # Llamada directa a la función importada para actualizar la misión
    actualizar_progreso_mision(db, player_id, tipo_objetivo='upgrade_room', objetivo_id=room_id) # type: ignore

    return {
        "status": "upgrade_started",
        "room_id": room_id,
        "completion_time": completion_time
    }

def check_and_complete_upgrades(db: Session):
    """
    Verifica y finaliza las mejoras de salas que han terminado su temporizador.
    """
    now = datetime.now(timezone.utc)
    
    finished_upgrades = db.query(ShipRoom).filter(
        ShipRoom.status == 'Upgrading', # type: ignore
        ShipRoom.upgrade_finish_time <= now # type: ignore
    ).all()

    for room in finished_upgrades:
        room.level += 1 # type: ignore
        room.status = 'Ready' # type: ignore
        room.upgrade_finish_time = None # type: ignore

    if finished_upgrades:
        db.commit()
    
    return len(finished_upgrades)