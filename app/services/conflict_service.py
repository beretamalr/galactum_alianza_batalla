from sqlalchemy.orm import Session
from typing import cast

from app.models.player_units import PlayerUnit
from app.models.tripulante import Tripulante
from app.models.player_equipment import PlayerEquipment
from app.models.ship import Ship
from app.services.recursos_service import agregar_recursos_jugador

# --- Modelos y datos de configuración (simulados para el ejemplo) ---
# En un proyecto real, estos datos vendrían de tablas de configuración en la BD.

# Simula la tabla `ConfigUnit` que define las estadísticas base de cada tipo de unidad.
CONFIG_UNITS_STATS = {
    "Infanteria": {"ataque": 10, "defensa": 10},
    "Tanque": {"ataque": 50, "defensa": 80},
}

# Simula la tabla `ConfigEquipment` que define los bonus de cada pieza de equipo.
CONFIG_EQUIPMENT_MODIFIERS = {
    "Exoesqueleto 'Bastion'": {"bonus_defensa_global": 25},
    "Mira 'Ojo de Aguila'": {"bonus_ataque_global": 15},
}

def _restar_unidades(db: Session, player_id: int, casualties: list[dict]):
    """Función interna para restar unidades perdidas en combate."""
    for casualty in casualties:
        unit_id = casualty['id']
        quantity_lost = casualty['quantity']

        player_unit = db.query(PlayerUnit).filter(
            PlayerUnit.player_id == player_id,
            PlayerUnit.unit_id == unit_id
        ).with_for_update().first()

        if player_unit:
            setattr(player_unit, 'quantity', max(0, cast(int, player_unit.quantity) - quantity_lost))

def resolve_conflict(db: Session, player_id: int, enemy_units: list[dict]):
    """
    Motor de cálculo y resolución de combate.
    1. Carga datos del jugador (unidades, tripulación, equipo).
    2. Calcula las estadísticas finales aplicando modificadores.
    3. Simula el combate contra las unidades enemigas.
    4. Aplica los resultados (pérdidas y recompensas) en una transacción.
    """
    
    # --- 1. Cargar datos del jugador ---
    player_units = db.query(PlayerUnit).filter(PlayerUnit.player_id == player_id).all()
    player_crew = db.query(Tripulante).filter(Tripulante.player_id == player_id).all()
    player_equipment = db.query(PlayerEquipment).filter(PlayerEquipment.player_id == player_id).all()
    player_ship = db.query(Ship).filter(Ship.owner_id == player_id).with_for_update().first()

    if not player_ship:
        raise ValueError("Nave del jugador no encontrada.")

    # --- 2. Calcular estadísticas finales del jugador ---
    player_stats = {"ataque": 0, "defensa": 0}

    # Sumar stats de unidades
    for unit in player_units:
        unit_config = CONFIG_UNITS_STATS.get(cast(str, unit.unit_id), {"ataque": 0, "defensa": 0})
        player_stats["ataque"] += unit_config["ataque"] * cast(int, unit.quantity)
        player_stats["defensa"] += unit_config["defensa"] * cast(int, unit.quantity)

    # Sumar stats de tripulación (ejemplo: cada punto de 'inteligencia' da +1 ataque/defensa)
    for member in player_crew:
        player_stats["ataque"] += cast(int, member.inteligencia)
        player_stats["defensa"] += cast(int, member.resistencia)

    # Aplicar modificadores de equipamiento
    for item in player_equipment:
        modifier = CONFIG_EQUIPMENT_MODIFIERS.get(cast(str, item.item_id))
        if modifier:
            player_stats["ataque"] += modifier.get("bonus_ataque_global", 0) * cast(int, item.quantity)
            player_stats["defensa"] += modifier.get("bonus_defensa_global", 0) * cast(int, item.quantity)

    # --- 3. Calcular estadísticas del enemigo y simular combate ---
    enemy_stats = {"ataque": 0, "defensa": 0}
    for unit in enemy_units:
        unit_config = CONFIG_UNITS_STATS.get(unit["id"], {"ataque": 0, "defensa": 0})
        enemy_stats["ataque"] += unit_config["ataque"] * unit["quantity"]
        enemy_stats["defensa"] += unit_config["defensa"] * unit["quantity"]

    # --- Simulación de combate muy simplificada ---
    # Comparamos el poder total (ataque + defensa)
    player_power = player_stats["ataque"] + player_stats["defensa"]
    enemy_power = enemy_stats["ataque"] + enemy_stats["defensa"]

    # Declaración de variables de resultado
    outcome: str
    troop_casualties: list[dict] = []
    resources_gained: list[dict] = []
    damage_taken = 0

    if player_power > enemy_power:
        outcome = "win"
        # El jugador gana, sufre 10% de bajas y recibe 100% de recompensas
        damage_taken = int(enemy_stats["ataque"] * 0.1) # Recibe 10% del ataque enemigo como daño
        for unit in player_units:
            casualties_count = int(cast(int, unit.quantity) * 0.1)
            if casualties_count > 0:
                troop_casualties.append({"id": unit.unit_id, "quantity": casualties_count})
        
        resources_gained = [{"id": "Roderitium", "quantity": 1000}, {"id": "Kliptium", "quantity": 200}]
    else:
        outcome = "loss"
        # El jugador pierde, sufre 80% de bajas y no recibe recompensas
        damage_taken = int(enemy_stats["ataque"] * 0.8) # Recibe 80% del ataque enemigo como daño
        for unit in player_units:
            casualties_count = int(cast(int, unit.quantity) * 0.8)
            if casualties_count > 0:
                troop_casualties.append({"id": unit.unit_id, "quantity": casualties_count})
        
        resources_gained = []

    # --- 4. Aplicar resultados en la transacción de BD ---
    # Aplicar daño a la nave
    setattr(player_ship, 'health', max(0, cast(int, player_ship.health) - damage_taken))

    # Restar bajas de unidades
    if troop_casualties:
        _restar_unidades(db, player_id, troop_casualties)

    # Añadir recursos ganados
    if resources_gained:
        agregar_recursos_jugador(db, player_id, resources_gained)

    # --- 5. Devolver el resultado final ---
    return {
        "outcome": outcome,
        "casualties": troop_casualties,
        "rewards": resources_gained,
        "damage_taken": damage_taken
    }