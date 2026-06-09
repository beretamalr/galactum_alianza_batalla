# app/services/job_queue_service.py
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.crafting import Recipe
from app.models.ship_rooms import ShipRoom
from app.services.recursos_service import verificar_y_consumir_recursos
from app.services.ship import get_player_ship_stats
import json
from datetime import datetime, timedelta, timezone
from typing import cast


def obtener_jobs(db: Session, player_id: int, tipo: str):
    """
    Obtiene los trabajos pendientes de un jugador para un tipo específico.
    """
    jobs = db.query(Job).filter(
        Job.player_id == player_id,
        Job.job_type == tipo,
        Job.status == 'pending'
    ).all()
    return jobs

def iniciar_trabajo_crafteo(db: Session, player_id: int, recipe_id: str):
    """
    Valida y crea un nuevo trabajo de crafteo en la cola.
    Es una operación transaccional.
    """
    # 1. Cargar la receta
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise ValueError(f"Receta '{recipe_id}' no encontrada.")

    # Asumimos que el modelo Recipe tiene estos campos
    required_level = getattr(recipe, 'required_room_level', 1)
    production_time = getattr(recipe, 'production_time_seconds', 60) # Default 1 min
    room_type = cast(str, recipe.type) # 'fabrica' o 'armeria'

    # 2. Validación de Prerrequisito de Nivel de Sala
    player_room = db.query(ShipRoom).filter(
        ShipRoom.player_id == player_id,
        ShipRoom.room_id == room_type
    ).first()

    if not player_room or cast(int, player_room.level) < required_level:
        raise PermissionError(f"Se requiere '{room_type}' a nivel {required_level}.")

    # 3. Validación y Consumo de Recursos
    try:
        costo_lista = json.loads(cast(str, recipe.ingredients))
        verificar_y_consumir_recursos(db, player_id, costo_lista)
    except (json.JSONDecodeError, TypeError):
        raise ValueError("Formato de ingredientes de receta inválido.")
    except Exception as e:
        raise ValueError(f"Recursos insuficientes: {e}") from e

    # 4. Añadir nuevo trabajo a la cola
    completion_time = datetime.now(timezone.utc) + timedelta(seconds=production_time)

    nuevo_trabajo = Job(
        player_id=player_id,
        job_type='crafting',
        related_id=recipe_id,
        completion_time=completion_time,
        status='pending'
    )
    db.add(nuevo_trabajo)
    db.flush() # Para obtener el ID del trabajo antes del commit

    # 5. Devolver el trabajo creado
    return nuevo_trabajo

def start_mining_job(db: Session, user_id: str, asteroid_id: str):
    """
    Valida e inicia un trabajo de minería.
    """
    # 1. Validación: ¿Hay otro trabajo de minería activo?
    existing_mining_job = db.query(Job).filter(
        Job.player_id == user_id, # Asumimos que Job.player_id puede ser el user_id (UUID)
        Job.job_type == 'mining',
        Job.status == 'pending'
    ).first()
    if existing_mining_job:
        raise Exception("Ya hay un trabajo de minería en curso.")

    # 2. Validación: ¿Existe el asteroide?
    # Mock de datos de asteroides. En un sistema real, esto vendría de la BD.
    asteroids_config = {
        "AST-001": {"mineral_level": 5, "resource_id": "Roderitium"},
        "AST-002": {"mineral_level": 10, "resource_id": "Kliptium"}
    }
    asteroid = asteroids_config.get(asteroid_id)
    if not asteroid:
        raise ValueError("Asteroide no encontrado.")

    # 3. Cálculo de Tiempo
    player_stats = get_player_ship_stats(db, user_id)
    extractor_level = player_stats["extractor_level"]
    if extractor_level == 0:
        raise ValueError("El nivel del extractor no puede ser cero.")

    # Fórmula: (Nivel del Mineral * 60 segundos) / Nivel del Extractor
    duration_seconds = (asteroid["mineral_level"] * 60) / extractor_level
    completion_time = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)

    # 4. Transacción: Registrar el trabajo en la cola
    nuevo_trabajo = Job(
        player_id=user_id, # Asumimos que Job.player_id puede ser el user_id (UUID)
        job_type='mining',
        related_id=asteroid_id,
        completion_time=completion_time,
        status='pending'
    )
    db.add(nuevo_trabajo)
    db.flush()

    # 5. Respuesta
    return nuevo_trabajo

def procesar_jobs_completados(db: Session):
    """
    Busca y procesa todos los trabajos que han alcanzado su tiempo de finalización.
    Esta función debería ser llamada periódicamente por un worker de fondo.
    """
    now = datetime.now(timezone.utc)
    # Se ajusta la consulta para ser más clara para el analizador estático.
    jobs_a_procesar = db.query(Job).filter(Job.status == 'pending')\
                                   .filter(Job.completion_time <= now)\
                                   .with_for_update().all()

    resultados = []
    for job in jobs_a_procesar:
        # La variable `job` es una instancia del modelo Job.
        # Las comparaciones y asignaciones directas a veces confunden a Pylance.
        # Usamos # type: ignore para suprimir el falso positivo de Pylance.
        if job.job_type == 'crafting': # type: ignore
            # Lógica para añadir el item `job.related_id` al inventario de `job.player_id`
            pass
        elif job.job_type == 'mining': # type: ignore
            # Lógica para añadir los recursos del asteroide `job.related_id` al jugador
            pass

        # Usamos setattr para evitar el falso positivo de Pylance "Cannot assign to attribute".
        setattr(job, 'status', 'completed')
        resultados.append(job)

    return resultados