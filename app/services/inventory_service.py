# app/services/inventory_service.py
from sqlalchemy.orm import Session
from app.models.player_equipment import PlayerEquipment
from app.models.inventory import Inventory # Importamos el modelo de inventario de recursos


def obtener_equipo(db: Session, player_id: int):
    """
    Obtiene el equipamiento de un jugador.
    NOTA: Para añadir el 'name', se necesitaría un JOIN con una tabla de ítems.
    """
    equipment = db.query(PlayerEquipment).filter(PlayerEquipment.player_id == player_id).all()
    return [{"item_id": item.item_id, "name": item.item_id, "quantity": item.quantity} for item in equipment]

def agregar_equipo(db: Session, player_id: int, item_id: str, quantity: int):
    """
    Añade una cantidad de un ítem de equipamiento al inventario de un jugador.
    Maneja la lógica de INSERT/UPDATE.
    """
    player_item = db.query(PlayerEquipment).filter(
        PlayerEquipment.player_id == player_id,
        PlayerEquipment.item_id == item_id
    ).with_for_update().first()

    if player_item:
        player_item.quantity += quantity # type: ignore
    else:
        new_player_item = PlayerEquipment(
            player_id=player_id,
            item_id=item_id,
            quantity=quantity
        )
        db.add(new_player_item)

def agregar_recurso(db: Session, player_id: int, resource_id: int, quantity: int):
    """
    Añade una cantidad de un recurso al inventario de un jugador.
    Maneja la lógica de INSERT/UPDATE para la tabla 'inventory'.
    """
    player_resource = db.query(Inventory).filter(
        Inventory.player_id == player_id,
        Inventory.resource_id == resource_id
    ).with_for_update().first()

    if player_resource:
        player_resource.quantity += quantity
    else:
        new_player_resource = Inventory(
            player_id=player_id,
            resource_id=resource_id,
            quantity=quantity
        )
        db.add(new_player_resource)

def crear_inventario_inicial(db: Session, player_id: int):
    """
    Crea el inventario inicial de recursos para un nuevo jugador usando una inserción masiva.
    """
    starter_items = [
        # Supervivencia (Crafteo de Comida)
        {"player_id": player_id, "resource_id": 3, "quantity": 10},  # Material Orgánico
        {"player_id": player_id, "resource_id": 7, "quantity": 10},  # H2O
        # Energía (Crafteo de Batería)
        {"player_id": player_id, "resource_id": 4, "quantity": 10},  # Litium
        {"player_id": player_id, "resource_id": 5, "quantity": 10},  # Copper
        # Combustible
        {"player_id": player_id, "resource_id": 1, "quantity": 20},  # Kliptium
    ]
    
    # Usamos bulk_insert_mappings para una inserción eficiente de todos los items.
    db.bulk_insert_mappings(Inventory, starter_items) # type: ignore
