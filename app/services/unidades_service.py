# app/services/unidades_service.py
from sqlalchemy.orm import Session
import json

from app.models.config_unit_recipes import ConfigUnitRecipe
from app.models.player_units import PlayerUnit
from app.services import recursos_service
from app.services import misiones_service

def _agregar_unidad(db: Session, player_id: int, unit_id: str, quantity: int):
    """
    Función interna para añadir unidades a un jugador.
    Maneja la lógica de INSERT/UPDATE.
    """
    player_unit = db.query(PlayerUnit).filter(
        PlayerUnit.player_id == player_id,
        PlayerUnit.unit_id == unit_id
    ).with_for_update().first()

    if player_unit:
        player_unit.quantity += quantity  # type: ignore
    else:
        new_player_unit = PlayerUnit(
            player_id=player_id,
            unit_id=unit_id,
            quantity=quantity
        )
        db.add(new_player_unit)

def create_unit(db: Session, player_id: int, unit_id: str, quantity: int = 1):
    """
    Lógica de negocio para crear una o más unidades. Es una operación transaccional.
    El commit/rollback debe ser manejado por el endpoint que la llama.
    """
    # 1. Buscar la receta de la unidad
    recipe = db.query(ConfigUnitRecipe).filter(ConfigUnitRecipe.unit_id == unit_id).first()
    if not recipe:
        raise Exception(f"Receta para la unidad '{unit_id}' no encontrada.")

    # 2. Cargar y calcular el costo total
    costo_unitario = json.loads(recipe.resource_cost_json)  # type: ignore
    costo_total = [{"id": item["id"], "quantity": item["quantity"] * quantity} for item in costo_unitario]

    # 3. Llamar al servicio de recursos para consumir el costo
    # Si no hay suficientes recursos, lanzará una excepción y la transacción se revertirá.
    recursos_service.verificar_y_consumir_recursos(db, player_id, costo_total)

    # 4. Si tiene éxito, llamar a la función interna para añadir la(s) unidad(es)
    _agregar_unidad(db, player_id, unit_id, quantity)

    # 5. Hook de Misión: Notificar al servicio de misiones sobre la creación
    misiones_service.actualizar_progreso_mision(
        db, player_id, tipo_objetivo='create_unit', objetivo_id=unit_id, cantidad=quantity
    )

    # El commit se maneja en el endpoint
    return {
        "unit_type_id": unit_id,
        "created_quantity": quantity
    }