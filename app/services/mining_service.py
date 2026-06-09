# app/services/mining_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from app.models.asteroid import Asteroid
from app.models.user import User
from app.models.crafting import CatalogoItem
from app.schemas.mining import MiningInfoResponse, MiningClaimResponse
from app.services.inventory_service import agregar_recurso

# Constante de configuración para la velocidad de minado.
# Representa 1 segundo por cada unidad de recurso.
MINING_SPEED_SECONDS = 2

def start_mining(db: Session, user: User, asteroid_name: str) -> MiningInfoResponse:
    """
    Inicia el proceso de minado en un asteroide, incluyendo el nombre del recurso.
    La duración total se calcula en base a la cantidad de recursos y la velocidad de minado.
    """
    # Modificar la consulta para incluir el join y obtener el nombre del recurso
    query_result = db.query(Asteroid, CatalogoItem.nombre)\
        .join(CatalogoItem, Asteroid.resource_id == CatalogoItem.id)\
        .filter(Asteroid.asteroid == asteroid_name)\
        .with_for_update().first()

    if not query_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asteroide no encontrado.",
        )
    
    asteroid, resource_name = query_result

    if not asteroid.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asteroide inactivo.",
        )

    if asteroid.mined_by_id is not None and str(asteroid.mined_by_id) != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asteroide ocupado. Minado termina en: {asteroid.mining_finish_at}",
        )

    # Si el mismo usuario ya está minando, devuelve el estado actual.
    if asteroid.mined_by_id is not None and str(asteroid.mined_by_id) == str(user.id) and asteroid.mining_finish_at:
        now = datetime.utcnow()
        total_duration_seconds = asteroid.cantidad_restante * MINING_SPEED_SECONDS
        total_duration = timedelta(seconds=total_duration_seconds)
        start_time_approx = asteroid.mining_finish_at - total_duration
        
        duration_left = timedelta(seconds=0)
        if now < asteroid.mining_finish_at:
             duration_left = asteroid.mining_finish_at - now

        return MiningInfoResponse(
            estado="already_mining",
            tiempo_inicio=start_time_approx,
            tiempo_fin=asteroid.mining_finish_at,
            duracion_segundos=int(duration_left.total_seconds()),
            rendimiento_esperado=asteroid.cantidad_restante,
            recurso_id=asteroid.resource_id,
            velocidad_minado=MINING_SPEED_SECONDS,
            nombre_recurso=resource_name,
        )

    # --- Lógica de Minado Escalable ---
    duration_seconds = asteroid.cantidad_restante * MINING_SPEED_SECONDS
    duration = timedelta(seconds=duration_seconds)
    now = datetime.utcnow()
    finish_time = now + duration

    # Actualiza el asteroide para bloquearlo para este usuario.
    asteroid.mined_by_id = str(user.id)
    asteroid.mining_finish_at = finish_time
    db.commit()
    db.refresh(asteroid)

    return MiningInfoResponse(
        estado="mining_started",
        tiempo_inicio=now,
        tiempo_fin=finish_time,
        duracion_segundos=duration_seconds,
        rendimiento_esperado=asteroid.cantidad_restante,
        recurso_id=asteroid.resource_id,
        velocidad_minado=MINING_SPEED_SECONDS,
        nombre_recurso=resource_name,
    )

def confirma_mining(db: Session, user: User, asteroid_name: str) -> MiningClaimResponse:
    """
    Confirma y reclama los recursos minados hasta el momento (Minado Parcial).
    El asteroide se desbloquea siempre después de reclamar.
    """
    # Modificar la consulta para incluir el join y obtener el nombre del recurso
    query_result = db.query(Asteroid, CatalogoItem.nombre)\
        .join(CatalogoItem, Asteroid.resource_id == CatalogoItem.id)\
        .filter(Asteroid.asteroid == asteroid_name)\
        .with_for_update().first()

    if not query_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asteroide no encontrado.")

    asteroid, resource_name = query_result

    if not asteroid.mined_by_id or str(asteroid.mined_by_id) != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para reclamar los recursos de este asteroide.",
        )
    
    if not asteroid.mining_finish_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Estado de minado inconsistente: no hay un tiempo de finalización registrado.",
        )

    # --- Lógica de Reclamo Parcial ---
    
    # 1. Deducir el tiempo de inicio original.
    total_time_needed_seconds = asteroid.cantidad_restante * MINING_SPEED_SECONDS
    total_time_needed = timedelta(seconds=total_time_needed_seconds)
    start_time = asteroid.mining_finish_at - total_time_needed

    # 2. Calcular la cantidad extraída basada en el tiempo transcurrido.
    elapsed_seconds = (datetime.utcnow() - start_time).total_seconds()
    cantidad_extraida = int(elapsed_seconds / MINING_SPEED_SECONDS)

    # 3. Validaciones
    if cantidad_extraida < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No has minado lo suficiente para reclamar al menos 1 unidad.",
        )

    # Limitar la extracción a la cantidad máxima disponible.
    if cantidad_extraida > asteroid.cantidad_restante:
        cantidad_extraida = asteroid.cantidad_restante

    resource_id = asteroid.resource_id

    # --- Actualización de la Base de Datos ---
    # Añadir al inventario del jugador.
    if user.jugador:
        agregar_recurso(db=db, player_id=user.jugador.id, resource_id=resource_id, quantity=cantidad_extraida)
    else:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error de consistencia: usuario sin jugador asociado.")

    # Restar del asteroide.
    asteroid.cantidad_restante -= cantidad_extraida

    # IMPORTANTE: Siempre desbloquear el asteroide para que pueda ser minado de nuevo.
    asteroid.mined_by_id = None
    asteroid.mining_finish_at = None

    # Si el asteroide se agota, desactivarlo y programar su reaparición.
    if asteroid.cantidad_restante <= 0:
        asteroid.is_active = False
        asteroid.reaparecer_en = datetime.utcnow() + timedelta(minutes=10)

    db.commit()

    return MiningClaimResponse(
        nombre_recurso=resource_name,
        cantidad_agregada=cantidad_extraida,
        cantidad_restante_asteroide=asteroid.cantidad_restante
    )
