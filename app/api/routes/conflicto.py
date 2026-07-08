from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.inventory import Inventory
from app.models.jugador import Jugador
from app.models.ship import Ship
from app.models.user import User
from app.services.auth import get_current_user


router = APIRouter(
    prefix="/conflicto",
    tags=["Conflictos y Combates"],
)


def _to_int(value, fallback: int = 0) -> int:
    try:
        if value is None:
            return fallback
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _get_player_and_ship(
    db: Session,
    current_user: User,
    lock_ship: bool = False,
) -> tuple[Jugador, Ship]:
    jugador = (
        db.query(Jugador)
        .filter(Jugador.user_id == current_user.id)
        .first()
    )

    if not jugador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el perfil de jugador asociado al usuario.",
        )

    ship_query = db.query(Ship).filter(Ship.owner_id == current_user.id)

    if lock_ship:
        ship_query = ship_query.with_for_update()

    ship = ship_query.first()

    if not ship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró una nave asociada al jugador.",
        )

    return jugador, ship


def _calculate_player_power(
    jugador: Jugador,
    ship: Ship,
    naves_enviadas: int = 1,
) -> int:
    base_power = _to_int(jugador.power, 0)
    ship_level = _to_int(ship.level, 1)
    hull_current = _to_int(ship.hull_current, 0)
    shield_current = _to_int(ship.shield_current, 0)
    energy_current = _to_int(ship.energy_current, 0)

    return (
        base_power
        + (ship_level * 120)
        + int(hull_current * 0.25)
        + int(shield_current * 0.8)
        + int(energy_current * 0.3)
        + (max(1, naves_enviadas) * 150)
    )


def _get_conflict(db: Session, conflict_id: int):
    conflict = db.execute(
        text(
            """
            SELECT
                id,
                enemy_faction,
                sector,
                state,
                danger,
                enemy_power,
                reward_resource_id,
                reward_resource_name,
                reward_quantity,
                energy_cost,
                hull_damage_win,
                hull_damage_loss,
                is_active
            FROM galactum_conflicts
            WHERE id = :conflict_id
              AND is_active = TRUE
            """
        ),
        {"conflict_id": conflict_id},
    ).mappings().first()

    return conflict


def _reward_inventory(
    db: Session,
    player_id: int,
    resource_id: int,
    quantity: int,
) -> None:
    if quantity <= 0:
        return

    inventory_item = (
        db.query(Inventory)
        .filter(
            Inventory.player_id == player_id,
            Inventory.resource_id == resource_id,
        )
        .with_for_update()
        .first()
    )

    if inventory_item:
        inventory_item.quantity = _to_int(inventory_item.quantity, 0) + quantity
        return

    db.add(
        Inventory(
            player_id=player_id,
            resource_id=resource_id,
            quantity=quantity,
        )
    )


@router.get(
    "/activos",
    status_code=status.HTTP_200_OK,
    name="Listar conflictos activos",
)
def listar_conflictos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista conflictos PvE persistentes.

    La respuesta incluye el poder estimado del jugador para que Godot pueda
    mostrar si el combate parece favorable o riesgoso antes de atacar.
    """
    jugador, ship = _get_player_and_ship(db, current_user)
    player_power = _calculate_player_power(jugador, ship, 1)

    rows = db.execute(
        text(
            """
            SELECT
                id,
                enemy_faction,
                sector,
                state,
                danger,
                enemy_power,
                reward_resource_id,
                reward_resource_name,
                reward_quantity,
                energy_cost,
                hull_damage_win,
                hull_damage_loss
            FROM galactum_conflicts
            WHERE is_active = TRUE
            ORDER BY id ASC
            """
        )
    ).mappings().all()

    conflicts = []

    for row in rows:
        enemy_power = _to_int(row["enemy_power"], 0)
        expected_result = "Favorable" if player_power >= enemy_power else "Riesgoso"

        conflicts.append(
            {
                "id": row["id"],
                "facción_enemiga": row["enemy_faction"],
                "faccion_enemiga": row["enemy_faction"],
                "sector": row["sector"],
                "estado": row["state"],
                "peligro": row["danger"],
                "poder_enemigo": enemy_power,
                "poder_jugador": player_power,
                "resultado_estimado": expected_result,
                "energia_requerida": _to_int(row["energy_cost"], 0),
                "daño_estimado_victoria": _to_int(row["hull_damage_win"], 0),
                "daño_estimado_derrota": _to_int(row["hull_damage_loss"], 0),
                "recompensa": {
                    "resource_id": row["reward_resource_id"],
                    "recurso": row["reward_resource_name"],
                    "cantidad": row["reward_quantity"],
                    "unidad": "unidades",
                },
            }
        )

    return conflicts


@router.post(
    "/atacar",
    status_code=status.HTTP_200_OK,
    name="Resolver ataque espacial",
)
def iniciar_ataque(
    conflicto_id: int,
    naves_enviadas: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Resuelve un combate simple contra una facción NPC.

    Si el jugador gana:
    - se descuenta energía,
    - la nave recibe daño menor,
    - se agregan recursos al inventario real.

    Si pierde:
    - se descuenta energía,
    - la nave recibe daño mayor,
    - no se entregan recompensas.
    """
    if naves_enviadas <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes enviar al menos 1 nave de combate.",
        )

    try:
        jugador, ship = _get_player_and_ship(
            db=db,
            current_user=current_user,
            lock_ship=True,
        )

        conflict = _get_conflict(db, conflicto_id)

        if not conflict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El conflicto solicitado no existe o ya no está activo.",
            )

        energy_cost = _to_int(conflict["energy_cost"], 0)
        current_energy = _to_int(ship.energy_current, 0)

        if current_energy < energy_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Energía insuficiente para iniciar el ataque. "
                    + "Necesitas "
                    + str(energy_cost)
                    + " de energía."
                ),
            )

        player_power = _calculate_player_power(
            jugador=jugador,
            ship=ship,
            naves_enviadas=naves_enviadas,
        )
        enemy_power = _to_int(conflict["enemy_power"], 0)

        victory = player_power >= enemy_power
        result = "victoria" if victory else "derrota"

        hull_damage = _to_int(
            conflict["hull_damage_win" if victory else "hull_damage_loss"],
            0,
        )

        reward_quantity = _to_int(conflict["reward_quantity"], 0) if victory else 0
        reward_resource_id = _to_int(conflict["reward_resource_id"], 0)
        reward_resource_name = str(conflict["reward_resource_name"])

        ship.energy_current = max(
            0,
            current_energy - energy_cost,
        )
        ship.hull_current = max(
            0,
            _to_int(ship.hull_current, 0) - hull_damage,
        )

        if victory and reward_resource_id > 0 and reward_quantity > 0:
            _reward_inventory(
                db=db,
                player_id=_to_int(jugador.id, 0),
                resource_id=reward_resource_id,
                quantity=reward_quantity,
            )

        db.execute(
            text(
                """
                INSERT INTO conflict_battle_logs (
                    player_id,
                    user_id,
                    conflict_id,
                    result,
                    player_power,
                    enemy_power,
                    hull_damage,
                    reward_resource_id,
                    reward_quantity
                )
                VALUES (
                    :player_id,
                    :user_id,
                    :conflict_id,
                    :result,
                    :player_power,
                    :enemy_power,
                    :hull_damage,
                    :reward_resource_id,
                    :reward_quantity
                )
                """
            ),
            {
                "player_id": jugador.id,
                "user_id": current_user.id,
                "conflict_id": conflict["id"],
                "result": result,
                "player_power": player_power,
                "enemy_power": enemy_power,
                "hull_damage": hull_damage,
                "reward_resource_id": reward_resource_id if victory else None,
                "reward_quantity": reward_quantity if victory else 0,
            },
        )

        db.commit()

        reward = {
            "resource_id": reward_resource_id,
            "recurso": reward_resource_name,
            "cantidad": reward_quantity,
            "unidad": "unidades",
        }

        message = (
            "Victoria en "
            + str(conflict["sector"])
            + ". Recompensa agregada al inventario."
            if victory
            else "Derrota en "
            + str(conflict["sector"])
            + ". La nave recibió daño y no obtuvo recompensa."
        )

        return {
            "status": result,
            "mensaje": message,
            "detalles": {
                "conflicto_id": conflict["id"],
                "facción_enemiga": conflict["enemy_faction"],
                "sector": conflict["sector"],
                "resultado": result,
                "poder_jugador": player_power,
                "poder_enemigo": enemy_power,
                "daño_casco": hull_damage,
                "energia_consumida": energy_cost,
                "energia_restante": ship.energy_current,
                "casco_restante": ship.hull_current,
                "recompensa": reward,
            },
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible resolver el combate: " + str(error),
        )
