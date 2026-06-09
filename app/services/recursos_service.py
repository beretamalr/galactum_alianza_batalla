# app/services/recursos_service.py
from sqlalchemy.orm import Session
from ..models.inventory import Inventory
from ..models.ship import Ship
from typing import cast

def obtener_inventario_jugador(db: Session, player_id: int):
    """
    Obtiene todo el inventario de un jugador.
    Responde a la Tarea 3.1 (GET /player/resources).
    """
    return db.query(Inventory).filter(Inventory.player_id == player_id).all()

def agregar_recursos_jugador(db: Session, player_id: int, lista_recursos: list):
    """
    Añade una lista de recursos al inventario de un jugador.
    No hace commit, permitiendo su uso en transacciones más grandes.
    lista_recursos: [{"id": "Roderitium", "quantity": 100}, ...]
    """
    for item in lista_recursos:
        resource_id = item['id']
        quantity = item['quantity']

        # Bloquea la fila para evitar race conditions al añadir
        db_inventory = db.query(Inventory).filter(
            Inventory.player_id == player_id,
            Inventory.resource_id == resource_id
        ).with_for_update().first()

        if db_inventory:
            db_inventory.quantity += quantity
        else:
            db_inventory = Inventory(
                player_id=player_id,
                resource_id=resource_id,
                quantity=quantity
            )
            db.add(db_inventory)

def verificar_y_consumir_recursos(db: Session, player_id: int, lista_costos: list):
    """
    Verifica si un jugador tiene suficientes recursos y los consume.
    Si no tiene, lanza una excepción. Es ATÓMICO dentro de una transacción mayor.
    No hace commit.
    lista_costos: [{"id": "Roderitium", "quantity": 50}, ...]
    """
    # 1. Fase de Verificación (para fallar rápido antes de modificar)
    for item in lista_costos:
        resource_id = item['id']
        quantity_needed = item['quantity']

        db_inventory = db.query(Inventory).filter(
            Inventory.player_id == player_id,
            Inventory.resource_id == resource_id
        ).first() # No se necesita with_for_update() para una simple lectura

        if not db_inventory or db_inventory.quantity < quantity_needed:
            raise Exception(f"Recursos insuficientes de: {resource_id}")

    # 2. Fase de Consumo (ahora con bloqueo para la escritura)
    for item in lista_costos:
        resource_id = item['id']
        quantity_to_consume = item['quantity']

        # Bloquea la fila para la transacción
        db_inventory = db.query(Inventory).filter(
            Inventory.player_id == player_id,
            Inventory.resource_id == resource_id
        ).with_for_update().first()

        # La verificación anterior asegura que esto no puede fallar,
        # pero es una buena práctica tener la lógica completa aquí.
        if not db_inventory or db_inventory.quantity < quantity_to_consume:
             # Este error no debería ocurrir si la verificación pasó, pero es una salvaguarda.
            raise Exception(f"Error de concurrencia o inconsistencia en {resource_id}")

        db_inventory.quantity -= quantity_to_consume

def convertir_recursos(db: Session, player_id: int, recipe_id: str):
    """
    Lógica de negocio para convertir un recurso en otro según una receta.
    Toda la operación es transaccional. El commit/rollback se maneja fuera.
    Responde a la Tarea 4.2 (POST /resources/convert).
    """
    # TODO: Mover las recetas a una tabla de configuración en la BD para mayor flexibilidad.
    if recipe_id == "Roderitium_a_Ore":
        costos = [{"id": "Roderitium", "quantity": 10}]
        productos = [{"id": "Ore", "quantity": 1}]
    else:
        # Lanza una excepción que el endpoint convertirá en un HTTP 404
        raise Exception("Receta no encontrada")

    # --- Lógica Transaccional Atómica ---
    # El endpoint que llama a esta función se encargará del try/except/commit/rollback.

    # 1. Consumir los recursos de entrada.
    # Si no hay suficientes, lanzará una excepción y la transacción se revertirá.
    verificar_y_consumir_recursos(db, player_id, costos)

    # 2. Añadir los recursos de salida.
    agregar_recursos_jugador(db, player_id, productos)

    # 3. Devolver un mensaje de éxito. El commit se hará en el endpoint.
    costo = costos[0]
    producto = productos[0]
    return {
        "status": "success",
        "message": f"Convertido {costo['quantity']} {costo['id']} a {producto['quantity']} {producto['id']}"
    }

def registrar_extraccion_recursos(db: Session, player_id: int, source_id: str, resources_gained: list):
    """
    Añade recursos de una fuente externa (minería) tras una validación.
    Es una operación transaccional.
    """
    # 1. Validación Crítica
    # En un sistema real, aquí habría una lógica compleja para evitar trampas.
    # Por ejemplo, verificar un log de combate, un trabajo completado, o la posición de la nave.
    
    # Ejemplo de validación: La nave del jugador debe estar cerca del asteroide.
    # Asumimos que los IDs de asteroides tienen un formato como "AST-XXX"
    if source_id.startswith("AST-"):
        # Mock de la posición del asteroide. En un caso real, esto vendría de la BD.
        asteroid_positions = {
            "AST-001": {"x": 150, "y": 340},
            "AST-002": {"x": 800, "y": 600},
        }
        asteroid_pos = asteroid_positions.get(source_id)
        if not asteroid_pos:
            raise Exception(f"Fuente de recursos inválida: {source_id}")

        ship = db.query(Ship).filter(Ship.owner_id == player_id).first()
        
        # Separamos las validaciones para claridad y para ayudar a Pylance
        if not ship:
            raise Exception("Validación de acción fallida: Nave no encontrada.")
        
        if cast(bool, ship.is_moving):
            raise Exception("Validación de acción fallida: La nave está en movimiento.")

        is_at_position = cast(float, ship.current_pos_x) == asteroid_pos['x'] and cast(float, ship.current_pos_y) == asteroid_pos['y']
        if not is_at_position:
            raise Exception("Validación de acción fallida: La nave no está en la ubicación correcta.")

    # 2. Ejecutar Transacción Atómica
    # Si la validación es exitosa, añadimos los recursos.
    agregar_recursos_jugador(db, player_id, resources_gained)

    return {"status": "success", "resources_added": resources_gained}