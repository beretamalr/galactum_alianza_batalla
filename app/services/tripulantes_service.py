from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import cast

from app.models.tripulante import Tripulante
from app.models.ship_rooms import ShipRoom
# Asumimos que estos modelos de configuración existen
# from app.models.config_crew import ConfigCrew
# from app.models.config_crew_upgrade import ConfigCrewUpgradeCost
from app.services.recursos_service import verificar_y_consumir_recursos
import logging

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def obtener_tripulantes(db: Session, player_id: int):
    """
    Obtiene todos los tripulantes de un jugador.
    Incluye el cálculo de bonificaciones activas.
    """
    tripulantes_db = db.query(Tripulante).filter(Tripulante.player_id == player_id).all()
    
    response = []
    for tripulante in tripulantes_db:
        # Lógica de cálculo de bonificaciones (ejemplo simple)
        # En un sistema real, aquí se sumarían bonos de equipo, sala, etc.
        bonus_por_nivel = cast(int, tripulante.nivel) - 1
        
        response.append({
            "id": tripulante.id,
            "nombre": tripulante.nombre,
            "nivel": tripulante.nivel,
            "especializacion": tripulante.especializacion,
            "slot_id": tripulante.slot_id,
            #"stats_base": {"inteligencia": tripulante.inteligencia, "resistencia": tripulante.resistencia, "carisma": tripulante.carisma, "percepcion": tripulante.percepcion, "suerte": tripulante.suerte, "agilidad": tripulante.agilidad},
            #"stats_calculadas": {"inteligencia": tripulante.inteligencia + bonus_por_nivel, "resistencia": tripulante.resistencia + bonus_por_nivel} # Ejemplo
        })
    return response

def asignar_tripulante(db: Session, player_id: int, crew_id: int, slot_id: int):
    """
    Asigna un tripulante a una sala de la nave.
    """
    # Verificar que el tripulante pertenece al jugador
    tripulante = db.query(Tripulante).filter(Tripulante.id == crew_id, Tripulante.player_id == player_id).first()
    if not tripulante:
        raise HTTPException(status_code=404, detail="Tripulante no encontrado.")

    # Verificar que la sala pertenece al jugador
    sala = db.query(ShipRoom).filter(ShipRoom.id == slot_id, ShipRoom.player_id == player_id).first()
    if not sala:
        raise HTTPException(status_code=404, detail="Sala no encontrada.")

    # Verificar si la sala ya está ocupada
    if sala.tripulante:
        raise HTTPException(status_code=400, detail="La sala ya está ocupada.")

    # Desasignar el tripulante de cualquier otra sala
    if tripulante.slot_id is not None:
        sala_anterior = db.query(ShipRoom).filter(ShipRoom.id == tripulante.slot_id).first()
        if sala_anterior:
            # Esto es una inconsistencia de datos si ocurre, pero lo manejamos por si acaso
            logger.warning(f"Inconsistencia: El tripulante {crew_id} estaba en la sala {tripulante.slot_id} que ya no tiene referencia a él.")

    # Asignar a la nueva sala
    tripulante.slot_id = slot_id # type: ignore
    db.commit()
    db.refresh(tripulante)
    
    return {"status": "success", "message": f"Tripulante {tripulante.nombre} asignado a la sala {sala.room_id}."}

def especializar_tripulante(db: Session, player_id: int, crew_id: int, specialization_id: int):
    """
    Asigna una especialización a un tripulante.
    """
    tripulante = db.query(Tripulante).filter(Tripulante.id == crew_id, Tripulante.player_id == player_id).first()
    if not tripulante:
        raise HTTPException(status_code=404, detail="Tripulante no encontrado.")

    # Lógica de coste (ejemplo: 500 de 'Kliptium')
    coste_recurso = "Kliptium"
    coste_cantidad = 500
    verificar_y_consumir_recursos(db, player_id, [{"id": coste_recurso, "quantity": coste_cantidad}])
    
    # Validación de Nivel
    if cast(int, tripulante.nivel) < 10:
        raise PermissionError("Se requiere nivel 10 para la especialización.")

    # Validación de especialización (ejemplo)
    especializaciones_validas = {1: "Ingeniero", 2: "Científico", 3: "Táctico"}
    if specialization_id not in especializaciones_validas:
        raise ValueError("Especialización no válida.")

    # Actualizar especialización y recursos
    setattr(tripulante, 'especializacion', especializaciones_validas[specialization_id])

    return {"status": "success", "message": f"Tripulante {tripulante.nombre} ahora es {especializaciones_validas[specialization_id]}."}

def adquirir_tripulante(db: Session, player_id: int, crew_template_id: str):
    """
    Lógica de negocio para adquirir un nuevo tripulante.
    """
    # 1. OBTENER PLANTILLA Y COSTO DEL TRIPULANTE
    # En un caso real, esto vendría de la tabla `ConfigCrew`
    # crew_template = db.query(ConfigCrew).filter(ConfigCrew.id == crew_template_id).first()
    # if not crew_template:
    #     raise ValueError("El tipo de tripulante especificado no existe.")
    # costo = json.loads(crew_template.costo_adquisicion_data)
    # stats_base = json.loads(crew_template.stats_base_data)
    # nombre_base = crew_template.nombre_base
    
    # --- Mock de datos para el ejemplo ---
    if crew_template_id != "piloto_clase_c":
        raise ValueError("El tipo de tripulante especificado no existe.")
    costo = [{"id": "Roderitium", "quantity": 500}]
    stats_base = {"inteligencia": 5, "resistencia": 6, "carisma": 4, "percepcion": 7, "suerte": 5, "agilidad": 8}
    nombre_base = "Piloto Recluta"
    # --- Fin del Mock ---

    # 2. VERIFICAR Y CONSUMIR RECURSOS
    try:
        verificar_y_consumir_recursos(db, player_id, costo)
    except Exception as e:
        raise ValueError(f"Recursos insuficientes para adquirir tripulante: {e}") from e

    # 3. CREAR NUEVA INSTANCIA DEL TRIPULANTE
    nuevo_tripulante = Tripulante(
        player_id=player_id,
        nombre=nombre_base,
        nivel=1,
        **stats_base # Desempaqueta el diccionario de stats en los campos del modelo
    )
    db.add(nuevo_tripulante)
    db.flush() # Para que el objeto tenga su ID antes de devolverlo

    return nuevo_tripulante

def mejorar_tripulante(db: Session, player_id: int, crew_instance_id: int):
    """
    Lógica de negocio para mejorar (subir de nivel/rango) un tripulante.
    """
    # 1. VERIFICAR QUE EL TRIPULANTE PERTENECE AL JUGADOR
    tripulante = db.query(Tripulante).filter(
        Tripulante.id == crew_instance_id,
        Tripulante.player_id == player_id
    ).with_for_update().first()

    if not tripulante:
        raise ValueError("Tripulante no encontrado o no pertenece al jugador.")

    # 2. OBTENER COSTO Y REQUISITOS DE MEJORA
    # En un caso real, esto vendría de `ConfigCrewUpgradeCost`
    # upgrade_config = db.query(ConfigCrewUpgradeCost).filter(ConfigCrewUpgradeCost.nivel_actual == tripulante.nivel).first()
    # if not upgrade_config:
    #     raise ValueError("Nivel máximo alcanzado o no hay configuración para la mejora.")
    # costo = json.loads(upgrade_config.costo_mejora_data)
    # stats_incremento = json.loads(upgrade_config.stats_incremento_data)

    # --- Mock de datos para el ejemplo ---
    if cast(int, tripulante.nivel) >= 10: # Límite de nivel de ejemplo
        raise ValueError("Nivel máximo alcanzado.")
    costo = [{"id": "Kliptium", "quantity": 50 * cast(int, tripulante.nivel)}]
    stats_incremento = {"inteligencia": 1, "resistencia": 2, "carisma": 1, "percepcion": 1, "suerte": 1, "agilidad": 1}
    requisito_sala_id = "Fabrica" # Ejemplo de requisito
    requisito_sala_nivel = cast(int, tripulante.nivel) # El nivel de la fábrica debe ser >= al nivel del tripulante
    # --- Fin del Mock ---

    # 3. VERIFICAR PRERREQUISITOS (NIVEL DE SALA)
    sala_requerida = db.query(ShipRoom).filter(
        ShipRoom.player_id == player_id,
        ShipRoom.room_id == requisito_sala_id
    ).first()
    if sala_requerida is None:
        raise PermissionError(f"Se requiere la sala '{requisito_sala_id}' para mejorar.")
    
    if cast(int, sala_requerida.level) < requisito_sala_nivel:
        raise PermissionError(f"Se requiere '{requisito_sala_id}' a nivel {requisito_sala_nivel} para mejorar.")

    # 4. VERIFICAR Y CONSUMIR RECURSOS
    try:
        verificar_y_consumir_recursos(db, player_id, costo)
    except Exception as e:
        raise ValueError(f"Recursos insuficientes para la mejora: {e}") from e

    # 5. APLICAR LA MEJORA
    setattr(tripulante, 'nivel', cast(int, tripulante.nivel) + 1)
    for stat, incremento in stats_incremento.items():
        current_value = cast(int, getattr(tripulante, stat))
        setattr(tripulante, stat, current_value + incremento)

    return tripulante