from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import sqrt
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.asteroid import Asteroid
from app.models.crafting import CatalogoItem
from app.models.inventory import Inventory
from app.models.user import User
from app.services.auth import get_current_user


router = APIRouter(
    prefix="/mining",
    tags=["Minería"],
)

# Para demo: 1 hora simulada dura 30 segundos reales.
SECONDS_PER_SIMULATED_HOUR = 30
UNITS_PER_SIMULATED_HOUR = 10
ASTEROID_RESPAWN_MINUTES = 10


@router.get(
    "/asteroides",
    status_code=status.HTTP_200_OK,
    name="Escanear asteroides reales",
)
def listar_asteroides(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """
    Devuelve asteroides reales desde Neon.

    También informa si un asteroide está disponible, ocupado por otro jugador,
    en extracción por el usuario actual o listo para reclamar.
    """
    _reactivar_asteroides_agotados(db)

    resultados = (
        db.query(Asteroid, CatalogoItem)
        .join(CatalogoItem, Asteroid.resource_id == CatalogoItem.id)
        .filter(Asteroid.is_active.is_(True))
        .order_by(Asteroid.asteroid.asc())
        .all()
    )

    return [
        _serializar_asteroide(
            asteroid=asteroid,
            item=item,
            current_user=current_user,
        )
        for asteroid, item in resultados
    ]


@router.post(
    "/extraer",
    status_code=status.HTTP_200_OK,
    name="Iniciar extracción minera",
)
def iniciar_extraccion(
    asteroide_id: str = Query(..., min_length=1),
    horas: int = Query(1, ge=1, le=4),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Bloquea un asteroide para el usuario autenticado y deja una operación
    minera pendiente de reclamo.
    """
    asteroid, item = _obtener_asteroide_con_recurso(
        db=db,
        asteroide_id=asteroide_id,
        lock=True,
    )

    _validar_asteroide_activo(asteroid)

    if asteroid.cantidad_restante <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El asteroide no tiene recursos disponibles.",
        )

    if asteroid.mined_by_id is not None:
        if str(asteroid.mined_by_id) == str(current_user.id):
            return {
                "estado": "already_mining",
                "mensaje": "Ya tienes una extracción activa en este asteroide.",
                "asteroide": _serializar_asteroide(
                    asteroid=asteroid,
                    item=item,
                    current_user=current_user,
                ),
            }

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este asteroide está siendo minado por otro comandante.",
        )

    now = _now_for(None)
    duration_seconds = horas * SECONDS_PER_SIMULATED_HOUR
    finish_at = now + timedelta(seconds=duration_seconds)

    asteroid.mined_by_id = current_user.id
    asteroid.mining_finish_at = finish_at

    db.commit()
    db.refresh(asteroid)

    expected_yield = min(
        int(asteroid.cantidad_restante),
        horas * UNITS_PER_SIMULATED_HOUR,
    )

    return {
        "estado": "mining_started",
        "mensaje": (
            "Extracción iniciada. "
            + str(horas)
            + " hora(s) simulada(s) equivalen a "
            + str(duration_seconds)
            + " segundos reales."
        ),
        "detalles": {
            "asteroide_id": asteroid.asteroid,
            "nombre": _nombre_asteroide(asteroid),
            "recurso": str(item.nombre),
            "rendimiento_estimado": expected_yield,
            "tiempo_fin": _datetime_to_text(asteroid.mining_finish_at),
            "tiempo_restante_segundos": _seconds_until(asteroid.mining_finish_at),
        },
    }


@router.post(
    "/reclamar",
    status_code=status.HTTP_200_OK,
    name="Reclamar recursos minados",
)
def reclamar_recursos(
    asteroide_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Reclama recursos cuando la operación minera del usuario ya terminó.
    Suma los recursos al inventario real del jugador en Neon.
    """
    if current_user.jugador is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario autenticado no tiene perfil de jugador.",
        )

    asteroid, item = _obtener_asteroide_con_recurso(
        db=db,
        asteroide_id=asteroide_id,
        lock=True,
    )

    if asteroid.mined_by_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este asteroide no tiene una extracción activa.",
        )

    if str(asteroid.mined_by_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes reclamar recursos de una extracción ajena.",
        )

    seconds_left = _seconds_until(asteroid.mining_finish_at)

    if seconds_left > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La extracción aún no termina. Faltan "
                + str(seconds_left)
                + " segundo(s)."
            ),
        )

    cantidad_extraida = min(
        UNITS_PER_SIMULATED_HOUR,
        int(asteroid.cantidad_restante),
    )

    if cantidad_extraida <= 0:
        asteroid.mined_by_id = None
        asteroid.mining_finish_at = None
        asteroid.is_active = False
        asteroid.reaparecer_en = _now_for(asteroid.reaparecer_en) + timedelta(
            minutes=ASTEROID_RESPAWN_MINUTES
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El asteroide ya no tenía recursos disponibles.",
        )

    inventario = (
        db.query(Inventory)
        .filter(
            Inventory.player_id == int(current_user.jugador.id),
            Inventory.resource_id == int(asteroid.resource_id),
        )
        .with_for_update()
        .first()
    )

    if inventario is None:
        inventario = Inventory(
            player_id=int(current_user.jugador.id),
            resource_id=int(asteroid.resource_id),
            quantity=0,
        )
        db.add(inventario)
        db.flush()

    inventario.quantity = int(inventario.quantity or 0) + cantidad_extraida

    asteroid.cantidad_restante = int(asteroid.cantidad_restante) - cantidad_extraida
    asteroid.mined_by_id = None
    asteroid.mining_finish_at = None

    if asteroid.cantidad_restante <= 0:
        asteroid.cantidad_restante = 0
        asteroid.is_active = False
        asteroid.reaparecer_en = _now_for(asteroid.reaparecer_en) + timedelta(
            minutes=ASTEROID_RESPAWN_MINUTES
        )

    db.commit()
    db.refresh(inventario)
    db.refresh(asteroid)

    return {
        "estado": "claimed",
        "mensaje": (
            "Recursos reclamados: +"
            + str(cantidad_extraida)
            + " "
            + str(item.nombre)
            + "."
        ),
        "detalles": {
            "recurso": str(item.nombre),
            "cantidad_agregada": cantidad_extraida,
            "cantidad_actual_inventario": int(inventario.quantity),
            "cantidad_restante_asteroide": int(asteroid.cantidad_restante),
        },
    }


def _obtener_asteroide_con_recurso(
    db: Session,
    asteroide_id: str,
    lock: bool = False,
) -> tuple[Asteroid, CatalogoItem]:
    query = (
        db.query(Asteroid, CatalogoItem)
        .join(CatalogoItem, Asteroid.resource_id == CatalogoItem.id)
        .filter(Asteroid.asteroid == asteroide_id)
    )

    if lock:
        query = query.with_for_update()

    result = query.first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asteroide no encontrado.",
        )

    asteroid, item = result
    return asteroid, item


def _validar_asteroide_activo(asteroid: Asteroid) -> None:
    if asteroid.is_active:
        return

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="El asteroide está agotado o en reaparición.",
    )


def _reactivar_asteroides_agotados(db: Session) -> None:
    now = _now_for(None)

    asteroides = (
        db.query(Asteroid)
        .filter(Asteroid.is_active.is_(False))
        .filter(Asteroid.reaparecer_en.isnot(None))
        .all()
    )

    changed = False

    for asteroid in asteroides:
        reaparece_en = asteroid.reaparecer_en

        if reaparece_en is None:
            continue

        compare_now = _now_for(reaparece_en)

        if reaparece_en <= compare_now:
            asteroid.is_active = True
            asteroid.cantidad_restante = int(asteroid.cantidad_maxima or 50)
            asteroid.mined_by_id = None
            asteroid.mining_finish_at = None
            asteroid.reaparecer_en = None
            changed = True

    if changed:
        db.commit()


def _serializar_asteroide(
    asteroid: Asteroid,
    item: CatalogoItem,
    current_user: User,
) -> dict[str, Any]:
    is_mined_by_user = (
        asteroid.mined_by_id is not None
        and str(asteroid.mined_by_id) == str(current_user.id)
    )

    seconds_left = 0
    listo_para_reclamar = False
    estado = "Disponible"

    if asteroid.mined_by_id is not None:
        seconds_left = _seconds_until(asteroid.mining_finish_at)

        if is_mined_by_user:
            if seconds_left <= 0:
                estado = "Listo para reclamar"
                listo_para_reclamar = True
            else:
                estado = "Extrayendo"
        else:
            estado = "Ocupado"

    riqueza = _calcular_riqueza(
        int(asteroid.cantidad_restante or 0),
        int(asteroid.cantidad_maxima or 1),
    )

    return {
        "id": str(asteroid.asteroid),
        "nombre": _nombre_asteroide(asteroid),
        "recurso": str(item.nombre),
        "riqueza": riqueza,
        "distancia_al": _calcular_distancia(asteroid, current_user),
        "cantidad_disponible": int(asteroid.cantidad_restante or 0),
        "cantidad_maxima": int(asteroid.cantidad_maxima or 0),
        "estado": estado,
        "minado_por_usuario": is_mined_by_user,
        "tiempo_restante_segundos": max(0, seconds_left),
        "listo_para_reclamar": listo_para_reclamar,
        "x": float(asteroid.position_x or 0.0),
        "y": float(asteroid.position_y or 0.0),
    }


def _nombre_asteroide(asteroid: Asteroid) -> str:
    logical_id = str(asteroid.asteroid)
    return logical_id.replace("AST-", "Asteroide ").replace("-", " ").title()


def _calcular_riqueza(cantidad_restante: int, cantidad_maxima: int) -> str:
    if cantidad_maxima <= 0:
        return "Baja"

    ratio = cantidad_restante / cantidad_maxima

    if ratio >= 0.66:
        return "Alta"

    if ratio >= 0.33:
        return "Media"

    return "Baja"


def _calcular_distancia(asteroid: Asteroid, current_user: User) -> str:
    ship = getattr(current_user, "ship", None)

    ship_x = 0.0
    ship_y = 0.0

    if ship is not None:
        ship_x = float(getattr(ship, "current_pos_x", 0.0) or 0.0)
        ship_y = float(getattr(ship, "current_pos_y", 0.0) or 0.0)

    distance = sqrt(
        (float(asteroid.position_x or 0.0) - ship_x) ** 2
        + (float(asteroid.position_y or 0.0) - ship_y) ** 2
    )

    return str(round(distance / 1000.0, 2)) + " sectores"


def _seconds_until(target: datetime | None) -> int:
    if target is None:
        return 0

    now = _now_for(target)
    remaining = int((target - now).total_seconds())
    return max(0, remaining)


def _now_for(value: datetime | None) -> datetime:
    if value is not None and value.tzinfo is not None and value.utcoffset() is not None:
        return datetime.now(timezone.utc)

    return datetime.utcnow()


def _datetime_to_text(value: datetime | None) -> str | None:
    if value is None:
        return None

    return value.isoformat()
