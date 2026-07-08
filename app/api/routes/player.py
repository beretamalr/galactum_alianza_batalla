from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from typing import List, Any, Dict

from app.services.auth import get_current_user
from app.models.user import User
from app.models.jugador import Jugador
from app.models.ship import Ship
from app.models.alianzas import Alliance, AllianceJoinRequest
from app.models.misiones import MisionJugador, MisionMaestra
from app.models.tripulante import Tripulante
from app.models.inventory import Inventory
from app.models.crafting import CatalogoItem
from app.db.dependencies import get_db
from app.services import ship, ship_rooms_service
from app.schemas.player import InventoryResponse


router = APIRouter(prefix="/api/v1/player", tags=["player"])


def _get_jugador_actual(current_user: User) -> Jugador:
    if not current_user.jugador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jugador no encontrado para este usuario.",
        )

    return current_user.jugador


def _safe_count(
    db: Session,
    sql: str,
    params: dict[str, Any] | None = None,
) -> int:
    try:
        value = db.execute(text(sql), params or {}).scalar()
        return int(value or 0)
    except Exception:
        db.rollback()
        return 0


def _safe_rows(
    db: Session,
    sql: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    try:
        rows = db.execute(text(sql), params or {}).mappings().all()
        return [dict(row) for row in rows]
    except Exception:
        db.rollback()
        return []


def _dt(value: Any) -> str | None:
    if value is None:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


def _ship_payload(ship_row: Ship | None) -> dict[str, Any]:
    if ship_row is None:
        return {
            "existe": False,
            "nombre": "Sin nave registrada",
            "nivel": 0,
            "energia": "0 / 0",
            "escudo": "0 / 0",
            "casco": "0 / 0",
            "posicion": "X 0 | Y 0",
            "estado_movimiento": "Sin datos",
        }

    return {
        "existe": True,
        "nombre": str(ship_row.name),
        "nivel": int(ship_row.level or 1),
        "energia_actual": int(ship_row.energy_current or 0),
        "energia_maxima": int(ship_row.energy_max or 0),
        "escudo_actual": int(ship_row.shield_current or 0),
        "escudo_maximo": int(ship_row.shield_max or 0),
        "casco_actual": int(ship_row.hull_current or 0),
        "casco_maximo": int(ship_row.hull_max or 0),
        "capacidad_carga": int(ship_row.cargo_capacity or 0),
        "nivel_extractor": int(ship_row.extractor_level or 1),
        "posicion_x": float(ship_row.current_pos_x or 0.0),
        "posicion_y": float(ship_row.current_pos_y or 0.0),
        "en_movimiento": bool(ship_row.is_moving),
        "energia": f"{int(ship_row.energy_current or 0)} / {int(ship_row.energy_max or 0)}",
        "escudo": f"{int(ship_row.shield_current or 0)} / {int(ship_row.shield_max or 0)}",
        "casco": f"{int(ship_row.hull_current or 0)} / {int(ship_row.hull_max or 0)}",
        "posicion": f"X {round(float(ship_row.current_pos_x or 0.0), 2)} | Y {round(float(ship_row.current_pos_y or 0.0), 2)}",
        "estado_movimiento": "En movimiento" if bool(ship_row.is_moving) else "En espera",
    }


def _alliance_payload(alliance: Alliance | None, jugador: Jugador) -> dict[str, Any]:
    if alliance is None:
        return {
            "pertenece": False,
            "nombre": "Sin alianza",
            "tag": "---",
            "rol": "Sin alianza",
            "miembros": 0,
        }

    es_lider = int(alliance.leader_jugador_id or 0) == int(jugador.id)

    return {
        "pertenece": True,
        "id": int(alliance.id),
        "nombre": str(alliance.name),
        "tag": str(alliance.tag),
        "nivel": int(alliance.level or 1),
        "miembros": int(alliance.members_count or 0),
        "miembros_maximos": int(alliance.max_members or 0),
        "poder_total": str(alliance.power or "0"),
        "rol": "Líder" if es_lider else "Miembro",
        "es_lider": es_lider,
    }


def _inventory_payload(db: Session, jugador_id: int) -> dict[str, Any]:
    rows = (
        db.query(Inventory, CatalogoItem)
        .outerjoin(CatalogoItem, CatalogoItem.id == Inventory.resource_id)
        .filter(Inventory.player_id == jugador_id)
        .order_by(Inventory.quantity.desc(), Inventory.resource_id.asc())
        .all()
    )

    recursos: list[dict[str, Any]] = []
    total_unidades = 0

    for inventario, item in rows:
        cantidad = int(inventario.quantity or 0)
        total_unidades += cantidad
        recursos.append(
            {
                "resource_id": int(inventario.resource_id),
                "nombre": str(item.nombre) if item else f"Recurso #{inventario.resource_id}",
                "cantidad": cantidad,
                "tipo": str(item.tipo) if item else "recurso",
                "rareza": str(item.rareza) if item and item.rareza else "común",
            }
        )

    return {
        "total_tipos": len(recursos),
        "total_unidades": total_unidades,
        "recursos_principales": recursos[:5],
    }


def _missions_payload(db: Session, jugador_id: int) -> dict[str, Any]:
    estados = {
        "activa": 0,
        "completada": 0,
        "reclamada": 0,
    }

    rows = (
        db.query(MisionJugador.estado, func.count(MisionJugador.id))
        .filter(MisionJugador.jugador_id == jugador_id)
        .group_by(MisionJugador.estado)
        .all()
    )

    for estado, cantidad in rows:
        estados[str(estado)] = int(cantidad or 0)

    total = sum(estados.values())

    return {
        "total": total,
        "activas": estados.get("activa", 0),
        "completadas": estados.get("completada", 0),
        "reclamadas": estados.get("reclamada", 0),
    }


@router.get("/profile", name="Get player profile")
def get_profile(current_user: User = Depends(get_current_user)):
    """
    Devuelve la información básica del jugador autenticado.
    """
    jugador = _get_jugador_actual(current_user)

    data = {
        "nickname": jugador.nickname,
        "user_id": str(current_user.id),
        "player_id": jugador.id,
        "power": jugador.power,
        "alliance_id": jugador.alliance_id,
    }
    return {"status": "success", "data": data}


@router.get("/resumen", name="Resumen completo del comandante")
def get_player_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Entrega un resumen consolidado del jugador para la pantalla Perfil del Comandante.
    Usa datos reales de Neon: jugador, nave, inventario, misiones, alianza y combates.
    """
    jugador = _get_jugador_actual(current_user)

    ship_row = (
        db.query(Ship)
        .filter(Ship.owner_id == current_user.id)
        .first()
    )

    alliance = None
    if jugador.alliance_id is not None:
        alliance = (
            db.query(Alliance)
            .filter(Alliance.id == jugador.alliance_id)
            .first()
        )

    tripulantes_count = (
        db.query(Tripulante)
        .filter(Tripulante.player_id == jugador.id)
        .count()
    )

    pending_requests = 0
    if alliance is not None and int(alliance.leader_jugador_id or 0) == int(jugador.id):
        pending_requests = (
            db.query(AllianceJoinRequest)
            .filter(
                AllianceJoinRequest.alliance_id == alliance.id,
                AllianceJoinRequest.status == "pending",
            )
            .count()
        )

    battles_total = _safe_count(
        db,
        "SELECT COUNT(*) FROM conflict_battle_logs WHERE player_id = :player_id",
        {"player_id": jugador.id},
    )
    victories_total = _safe_count(
        db,
        "SELECT COUNT(*) FROM conflict_battle_logs WHERE player_id = :player_id AND LOWER(result) = 'victoria'",
        {"player_id": jugador.id},
    )

    return {
        "status": "success",
        "data": {
            "usuario": {
                "id": str(current_user.id),
                "username": str(current_user.username),
                "email": str(current_user.email),
            },
            "jugador": {
                "id": int(jugador.id),
                "nickname": str(jugador.nickname),
                "poder": int(jugador.power or 0),
            },
            "alianza": _alliance_payload(alliance, jugador),
            "nave": _ship_payload(ship_row),
            "inventario": _inventory_payload(db, int(jugador.id)),
            "misiones": _missions_payload(db, int(jugador.id)),
            "tripulacion": {
                "total": int(tripulantes_count or 0),
            },
            "combates": {
                "total": battles_total,
                "victorias": victories_total,
                "derrotas": max(0, battles_total - victories_total),
            },
            "solicitudes_alianza": {
                "pendientes_como_lider": int(pending_requests or 0),
            },
        },
    }


@router.get("/bitacora", name="Bitácora galáctica del comandante")
def get_player_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Construye una bitácora derivada desde datos persistentes.
    No requiere una tabla nueva: resume nave, alianza, recursos, misiones y combates.
    """
    jugador = _get_jugador_actual(current_user)
    eventos: list[dict[str, Any]] = []

    def add_event(
        tipo: str,
        titulo: str,
        descripcion: str,
        fecha: Any = None,
        estado: str = "info",
    ) -> None:
        eventos.append(
            {
                "tipo": tipo,
                "titulo": titulo,
                "descripcion": descripcion,
                "fecha": _dt(fecha),
                "estado": estado,
            }
        )

    add_event(
        "perfil",
        "Comandante autenticado",
        f"{jugador.nickname} ingresó con poder {int(jugador.power or 0)}.",
        None,
        "ok",
    )

    ship_row = (
        db.query(Ship)
        .filter(Ship.owner_id == current_user.id)
        .first()
    )
    if ship_row is not None:
        add_event(
            "nave",
            "Nave operativa",
            (
                f"{ship_row.name} | Nivel {int(ship_row.level or 1)} | "
                f"Energía {int(ship_row.energy_current or 0)}/{int(ship_row.energy_max or 0)} | "
                f"Casco {int(ship_row.hull_current or 0)}/{int(ship_row.hull_max or 0)}."
            ),
            None,
            "ok",
        )

    if jugador.alliance_id is not None:
        alliance = db.query(Alliance).filter(Alliance.id == jugador.alliance_id).first()
        if alliance is not None:
            rol = "líder" if int(alliance.leader_jugador_id or 0) == int(jugador.id) else "miembro"
            add_event(
                "alianza",
                "Alianza activa",
                f"Pertenece a {alliance.name} [{alliance.tag}] como {rol}.",
                alliance.created_at,
                "ok",
            )

    inventario = _inventory_payload(db, int(jugador.id))
    add_event(
        "inventario",
        "Bodega sincronizada",
        (
            f"Inventario con {inventario['total_tipos']} tipo(s) de recurso "
            f"y {inventario['total_unidades']} unidad(es) totales."
        ),
        None,
        "ok",
    )

    mission_rows = (
        db.query(MisionJugador, MisionMaestra)
        .join(MisionMaestra, MisionMaestra.mision_id == MisionJugador.mision_id)
        .filter(MisionJugador.jugador_id == jugador.id)
        .order_by(MisionJugador.id.desc())
        .limit(8)
        .all()
    )

    for registro, mision in mission_rows:
        estado = str(registro.estado)
        fecha = registro.reclamada_en if estado == "reclamada" else registro.aceptada_en
        add_event(
            "misión",
            f"Misión {estado}: {mision.titulo}",
            (
                f"Progreso {int(registro.progreso_actual or 0)}/"
                f"{int(mision.cantidad_requerida or 0)} | Dificultad {mision.dificultad}."
            ),
            fecha,
            "ok" if estado == "reclamada" else "warn",
        )

    battle_rows = _safe_rows(
        db,
        """
        SELECT
            cbl.created_at,
            cbl.result,
            cbl.player_power,
            cbl.enemy_power,
            cbl.hull_damage,
            cbl.reward_quantity,
            gc.enemy_faction,
            gc.sector
        FROM conflict_battle_logs cbl
        LEFT JOIN galactum_conflicts gc ON gc.id = cbl.conflict_id
        WHERE cbl.player_id = :player_id
        ORDER BY cbl.created_at DESC
        LIMIT 8
        """,
        {"player_id": jugador.id},
    )

    for battle in battle_rows:
        result = str(battle.get("result", "combate"))
        add_event(
            "conflicto",
            f"Combate: {result.upper()}",
            (
                f"Contra {battle.get('enemy_faction') or 'facción desconocida'} "
                f"en {battle.get('sector') or 'sector desconocido'} | "
                f"Poder {battle.get('player_power')} vs {battle.get('enemy_power')} | "
                f"Daño casco {battle.get('hull_damage')} | "
                f"Recompensa {battle.get('reward_quantity')} unidad(es)."
            ),
            battle.get("created_at"),
            "ok" if result.lower() == "victoria" else "danger",
        )

    if not eventos:
        add_event(
            "sistema",
            "Sin eventos",
            "Todavía no hay acciones registradas para este comandante.",
            None,
            "warn",
        )

    return {
        "status": "success",
        "total_eventos": len(eventos),
        "eventos": eventos,
    }


@router.get("/rooms", response_model=List[Dict[str, Any]], name="Get player ship rooms")
def get_ship_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado para este usuario.")

    salas = ship_rooms_service.obtener_info_salas(db, player_id=current_user.jugador.id)  # type: ignore
    return salas


@router.get("/stats", name="Get player final stats")
def get_player_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        stats = ship.get_player_ship_stats(db, str(current_user.id))
        return {"status": "success", "data": stats}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/resources", response_model=InventoryResponse, name="Get player resources")
def get_player_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado para este usuario.")

    inventario_con_detalles = db.query(
        Inventory.resource_id,
        Inventory.quantity,
        CatalogoItem.nombre,
        CatalogoItem.descripcion,
        CatalogoItem.tipo,
        CatalogoItem.rareza,
        CatalogoItem.imagen_url,
    ).join(
        CatalogoItem, Inventory.resource_id == CatalogoItem.id
    ).filter(
        Inventory.player_id == current_user.jugador.id
    ).all()

    inventario_enriquecido = [dict(item._mapping) for item in inventario_con_detalles]

    return InventoryResponse(recursos=inventario_enriquecido)


@router.get("/friends", name="Get player friends")
def get_friends(current_user: User = Depends(get_current_user)):
    data = [
        {"username": "aliado_1", "status": "online"},
        {"username": "aliado_2", "status": "offline"},
    ]
    return {"status": "success", "data": data}


@router.put("/settings", name="Update player settings")
def update_settings(
    settings: dict,
    current_user: User = Depends(get_current_user),
):
    return {"status": "success", "updated_settings": settings}
