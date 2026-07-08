from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.dependencies import get_db
from app.models.crafting import CatalogoItem
from app.models.inventory import Inventory
from app.models.misiones import MisionJugador, MisionMaestra
from app.models.user import User
from app.services.auth import get_current_user


router = APIRouter(
    prefix="/misiones",
    tags=["Misiones"],
)


@router.get(
    "/disponibles",
    status_code=status.HTTP_200_OK,
    name="Listar misiones disponibles reales",
)
def listar_misiones_disponibles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Devuelve el tablero real de misiones desde Neon.

    Incluye también el estado de cada misión para el jugador autenticado:
    disponible, activa, completada o reclamada.
    """
    jugador_id = _get_jugador_id(current_user)
    _actualizar_progreso_misiones(db, jugador_id)

    misiones = (
        db.query(MisionMaestra)
        .options(joinedload(MisionMaestra.objetivo_recurso))
        .filter(MisionMaestra.activa.is_(True))
        .order_by(MisionMaestra.mision_id.asc())
        .all()
    )

    estados = _obtener_estados_jugador(db, jugador_id)

    return {
        "status": "success",
        "misiones": [
            _serializar_mision_disponible(
                db=db,
                mision=mision,
                mision_jugador=estados.get(str(mision.mision_id)),
                jugador_id=jugador_id,
            )
            for mision in misiones
        ],
    }


@router.get(
    "/activas",
    status_code=status.HTTP_200_OK,
    name="Listar misiones del jugador",
)
def listar_misiones_jugador(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Devuelve las misiones aceptadas por el jugador y su progreso real.
    El progreso se calcula contra el inventario persistido en Neon.
    """
    jugador_id = _get_jugador_id(current_user)
    _actualizar_progreso_misiones(db, jugador_id)

    registros = (
        db.query(MisionJugador)
        .options(
            joinedload(MisionJugador.mision_maestra).joinedload(
                MisionMaestra.objetivo_recurso
            )
        )
        .filter(MisionJugador.jugador_id == jugador_id)
        .order_by(MisionJugador.id.asc())
        .all()
    )

    return {
        "status": "success",
        "misiones": [
            _serializar_mision_jugador(db=db, registro=registro, jugador_id=jugador_id)
            for registro in registros
            if registro.mision_maestra is not None
        ],
    }


@router.post(
    "/{mision_id}/aceptar",
    status_code=status.HTTP_200_OK,
    name="Aceptar misión real",
)
def aceptar_mision(
    mision_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Acepta una misión y la guarda en misiones_jugadores.
    """
    jugador_id = _get_jugador_id(current_user)

    mision = _obtener_mision(db, mision_id)

    existente = (
        db.query(MisionJugador)
        .filter(
            MisionJugador.jugador_id == jugador_id,
            MisionJugador.mision_id == str(mision.mision_id),
        )
        .first()
    )

    if existente is not None:
        _actualizar_un_progreso(db, existente, jugador_id)
        db.commit()
        db.refresh(existente)

        return {
            "status": "success",
            "mensaje": "La misión ya estaba aceptada.",
            "mision": _serializar_mision_jugador(
                db=db,
                registro=existente,
                jugador_id=jugador_id,
            ),
        }

    progreso = _calcular_progreso_actual(db, jugador_id, mision)
    estado = "completada" if progreso >= int(mision.cantidad_requerida or 1) else "activa"

    registro = MisionJugador(
        jugador_id=jugador_id,
        mision_id=str(mision.mision_id),
        progreso_actual=progreso,
        estado=estado,
    )

    db.add(registro)
    db.commit()
    db.refresh(registro)

    return {
        "status": "success",
        "mensaje": "Misión aceptada correctamente.",
        "mision": _serializar_mision_jugador(
            db=db,
            registro=registro,
            jugador_id=jugador_id,
        ),
    }


@router.post(
    "/{mision_id}/reclamar",
    status_code=status.HTTP_200_OK,
    name="Reclamar recompensa de misión",
)
def reclamar_mision(
    mision_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        jugador_id = _get_jugador_id(current_user)

        # IMPORTANTE:
        # No usar joinedload + with_for_update aquí.
        # PostgreSQL no permite FOR UPDATE sobre el lado nullable de un OUTER JOIN.
        registro = (
            db.query(MisionJugador)
            .filter(
                MisionJugador.jugador_id == jugador_id,
                MisionJugador.mision_id == mision_id,
            )
            .with_for_update()
            .first()
        )

        if registro is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Misión no aceptada por este jugador.",
            )

        mision_maestra = (
            db.query(MisionMaestra)
            .filter(MisionMaestra.mision_id == registro.mision_id)
            .first()
        )

        if mision_maestra is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La misión maestra no existe.",
            )

        if str(registro.estado) == "reclamada":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La recompensa de esta misión ya fue reclamada.",
            )

        _actualizar_un_progreso(
            db=db,
            registro=registro,
            jugador_id=jugador_id,
        )

        if str(registro.estado) != "completada":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La misión aún no está completada.",
            )

        recompensas = _parse_recompensas(
            str(mision_maestra.recompensa_data or "[]")
        )

        if not recompensas:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta misión no tiene recompensas configuradas.",
            )

        recursos_ganados = _agregar_recompensas(
            db=db,
            jugador_id=jugador_id,
            recompensas=recompensas,
        )

        registro.estado = "reclamada"
        registro.reclamada_en = datetime.now(timezone.utc)

        db.commit()
        db.refresh(registro)

        return {
            "status": "success",
            "mensaje": "Recompensa reclamada correctamente.",
            "recursos_ganados": recursos_ganados,
            "mision_id": registro.mision_id,
            "estado": registro.estado,
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al reclamar recompensa: " + str(error),
        )

def _get_jugador_id(current_user: User) -> int:
    if current_user.jugador is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario autenticado no tiene perfil de jugador.",
        )

    return int(current_user.jugador.id)


def _obtener_mision(db: Session, mision_id: str) -> MisionMaestra:
    mision = (
        db.query(MisionMaestra)
        .options(joinedload(MisionMaestra.objetivo_recurso))
        .filter(MisionMaestra.mision_id == mision_id)
        .first()
    )

    if mision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Misión no encontrada.",
        )

    if not bool(mision.activa):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La misión no está activa actualmente.",
        )

    return mision


def _obtener_estados_jugador(db: Session, jugador_id: int) -> dict[str, MisionJugador]:
    registros = (
        db.query(MisionJugador)
        .filter(MisionJugador.jugador_id == jugador_id)
        .all()
    )

    return {str(registro.mision_id): registro for registro in registros}


def _actualizar_progreso_misiones(db: Session, jugador_id: int) -> None:
    registros = (
        db.query(MisionJugador)
        .options(joinedload(MisionJugador.mision_maestra))
        .filter(MisionJugador.jugador_id == jugador_id)
        .all()
    )

    changed = False

    for registro in registros:
        if registro.mision_maestra is None:
            continue

        if _actualizar_un_progreso(db, registro, jugador_id):
            changed = True

    if changed:
        db.commit()


def _actualizar_un_progreso(
    db: Session,
    registro: MisionJugador,
    jugador_id: int,
) -> bool:
    if str(registro.estado) == "reclamada":
        return False

    mision = registro.mision_maestra

    if mision is None:
        return False

    progreso = _calcular_progreso_actual(db, jugador_id, mision)
    requerido = int(mision.cantidad_requerida or 1)
    progreso_limitado = min(progreso, requerido)
    nuevo_estado = "completada" if progreso >= requerido else "activa"

    changed = False

    if int(registro.progreso_actual or 0) != progreso_limitado:
        registro.progreso_actual = progreso_limitado
        changed = True

    if str(registro.estado) != nuevo_estado:
        registro.estado = nuevo_estado
        changed = True

    return changed


def _calcular_progreso_actual(
    db: Session,
    jugador_id: int,
    mision: MisionMaestra,
) -> int:
    tipo_objetivo = str(mision.tipo_objetivo or "tener_recurso")

    if tipo_objetivo != "tener_recurso":
        return 0

    resource_id = mision.objetivo_recurso_id

    if resource_id is None:
        return 0

    inventario = (
        db.query(Inventory)
        .filter(
            Inventory.player_id == jugador_id,
            Inventory.resource_id == int(resource_id),
        )
        .first()
    )

    if inventario is None:
        return 0

    return max(0, int(inventario.quantity or 0))


def _serializar_mision_disponible(
    db: Session,
    mision: MisionMaestra,
    mision_jugador: MisionJugador | None,
    jugador_id: int,
) -> dict[str, Any]:
    estado_jugador = "disponible"
    progreso_actual = _calcular_progreso_actual(db, jugador_id, mision)

    if mision_jugador is not None:
        estado_jugador = str(mision_jugador.estado)
        progreso_actual = int(mision_jugador.progreso_actual or 0)

    return _serializar_base_mision(
        mision=mision,
        progreso_actual=progreso_actual,
        estado_jugador=estado_jugador,
    )


def _serializar_mision_jugador(
    db: Session,
    registro: MisionJugador,
    jugador_id: int,
) -> dict[str, Any]:
    mision = registro.mision_maestra

    if mision is None:
        return {}

    return _serializar_base_mision(
        mision=mision,
        progreso_actual=int(registro.progreso_actual or 0),
        estado_jugador=str(registro.estado),
    )


def _serializar_base_mision(
    mision: MisionMaestra,
    progreso_actual: int,
    estado_jugador: str,
) -> dict[str, Any]:
    requerido = int(mision.cantidad_requerida or 1)
    recurso_objetivo = "Recurso"

    if mision.objetivo_recurso is not None:
        recurso_objetivo = str(mision.objetivo_recurso.nombre)

    recompensas = _parse_recompensas(str(mision.recompensa_data or "[]"))

    return {
        "id": str(mision.mision_id),
        "mision_id": str(mision.mision_id),
        "titulo": str(mision.titulo),
        "descripcion": str(mision.descripcion),
        "tipo_mision": str(mision.tipo_mision),
        "dificultad": str(mision.dificultad or "Fácil"),
        "tipo_objetivo": str(mision.tipo_objetivo or "tener_recurso"),
        "objetivo_recurso_id": int(mision.objetivo_recurso_id or 0),
        "objetivo_recurso": recurso_objetivo,
        "cantidad_requerida": requerido,
        "progreso_actual": min(int(progreso_actual or 0), requerido),
        "estado_jugador": estado_jugador,
        "recompensas": recompensas,
        "recompensa_texto": _formatear_recompensas(recompensas),
    }


def _parse_recompensas(raw_value: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(raw_value)
    except Exception:
        return []

    if not isinstance(parsed, list):
        return []

    recompensas: list[dict[str, Any]] = []

    for item in parsed:
        if not isinstance(item, dict):
            continue

        resource_id = item.get("resource_id", item.get("id", item.get("item_id")))
        cantidad = item.get("cantidad", item.get("quantity", 0))

        try:
            resource_id_int = int(resource_id)
            cantidad_int = int(cantidad)
        except Exception:
            continue

        if resource_id_int <= 0 or cantidad_int <= 0:
            continue

        recompensas.append(
            {
                "resource_id": resource_id_int,
                "cantidad": cantidad_int,
                "nombre": str(item.get("nombre", "Recurso")),
            }
        )

    return recompensas


def _agregar_recompensas(
    db: Session,
    jugador_id: int,
    recompensas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    recursos_ganados: list[dict[str, Any]] = []

    for recompensa in recompensas:
        resource_id = int(recompensa["resource_id"])
        cantidad = int(recompensa["cantidad"])

        inventario = (
            db.query(Inventory)
            .filter(
                Inventory.player_id == jugador_id,
                Inventory.resource_id == resource_id,
            )
            .with_for_update()
            .first()
        )

        if inventario is None:
            inventario = Inventory(
                player_id=jugador_id,
                resource_id=resource_id,
                quantity=0,
            )
            db.add(inventario)
            db.flush()

        inventario.quantity = int(inventario.quantity or 0) + cantidad

        item = db.query(CatalogoItem).filter(CatalogoItem.id == resource_id).first()
        nombre = str(item.nombre) if item is not None else str(recompensa.get("nombre", "Recurso"))

        recursos_ganados.append(
            {
                "resource_id": resource_id,
                "nombre": nombre,
                "cantidad": cantidad,
                "cantidad_actual": int(inventario.quantity),
            }
        )

    return recursos_ganados


def _formatear_recompensas(recompensas: list[dict[str, Any]]) -> str:
    if not recompensas:
        return "Sin recompensa definida"

    partes: list[str] = []

    for recompensa in recompensas:
        partes.append(
            "+"
            + str(recompensa.get("cantidad", 0))
            + " "
            + str(recompensa.get("nombre", "Recurso"))
        )

    return ", ".join(partes)
