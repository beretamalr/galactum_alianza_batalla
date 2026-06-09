# app/services/crafting_service.py
from sqlalchemy.orm import Session
from app.models.crafting import RecetaCrafteo, CatalogoItem
# Ya no necesitamos importar ShipRoom ni cast
from app.services.recursos_service import verificar_y_consumir_recursos, agregar_recursos_jugador

def craftear_recurso(db: Session, jugador_id: int, item_resultado_id: int, cantidad: int = 1):
    """
    Gestiona la lógica de crafteo simplificada.
    Valida la existencia del item y la receta, consume los materiales y entrega el producto.
    
    Args:
        item_resultado_id: ID del item que se desea fabricar (CatalogoItem.id).
    """
    
    # 1. VALIDAR QUE EL ITEM EXISTE (Opcional, pero recomendado para mensajes de error claros)
    item_obj = db.query(CatalogoItem).filter(CatalogoItem.id == item_resultado_id).first()
    if not item_obj:
        raise ValueError(f"El item con ID {item_resultado_id} no existe en el catálogo.")

    # 2. OBTENER LA RECETA (Lista de ingredientes)
    # Buscamos todas las filas donde este item es el resultado
    lineas_receta = db.query(RecetaCrafteo).filter(
        RecetaCrafteo.item_resultado_id == item_resultado_id
    ).all()

    if not lineas_receta:
        raise ValueError(f"El item '{item_obj.nombre}' no tiene una receta de crafteo definida.")

    # 3. PREPARAR LISTA DE RECURSOS
    # Convertimos los objetos SQLAlchemy al formato [{"id": int, "quantity": int}]
    recursos_entrada = [
        {"id": linea.item_requerido_id, "quantity": linea.cantidad * cantidad}
        for linea in lineas_receta
    ]
    
    # Asumimos producción de 1 unidad
    recursos_salida = [{"id": item_resultado_id, "quantity": cantidad}]

    # --- INICIO DE TRANSACCIÓN LÓGICA ---
    # La sesión de DB maneja la atomicidad real al hacer commit en el endpoint,
    # pero aquí aseguramos la lógica secuencial.

    # 4. CONSUMIR INGREDIENTES
    try:
        verificar_y_consumir_recursos(db, jugador_id, recursos_entrada)
    except Exception as e:
        # Relanzamos el error con el nombre del item para que el usuario sepa qué falló
        raise ValueError(f"No tienes suficientes materiales para craftear '{item_obj.nombre}'. {e}") from e

    # 5. ENTREGAR PRODUCTO
    agregar_recursos_jugador(db, jugador_id, recursos_salida)

    # --- FIN DE TRANSACCIÓN LÓGICA ---

    return {
        "status": "success",
        "mensaje": f"Has crafteado 1x {item_obj.nombre}",
        "item_id": item_resultado_id,
        "consumidos": recursos_entrada,
        "producidos": recursos_salida
    }