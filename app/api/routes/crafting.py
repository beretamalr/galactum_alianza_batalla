from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.crafting import CatalogoItem
from app.models.inventory import Inventory
from app.models.ship import Ship
from app.models.user import User
from app.services.auth import get_current_user
from app.services.ship import get_or_create_ship


router = APIRouter(
    prefix="/crafting",
    tags=["Fabricación y Mejoras"],
)


RESOURCE_IDS = {
    "Kliptium": 1,
    "Material Orgánico": 3,
    "Litium": 4,
    "Copper": 5,
    "H2O": 7,
}


BASE_RECIPES = [
    {
        "id": "reactor_mk2",
        "nombre": "Reactor de energía MK2",
        "categoria": "Nave",
        "descripcion": "Aumenta la energía máxima de la nave y recarga parte del reactor.",
        "efecto": "Energía máxima +25",
        "maximo": 225,
        "stat": "energy_max",
        "materiales": [
            {"resource_id": RESOURCE_IDS["Litium"], "nombre": "Litium", "cantidad": 10},
            {"resource_id": RESOURCE_IDS["Copper"], "nombre": "Copper", "cantidad": 8},
            {"resource_id": RESOURCE_IDS["Kliptium"], "nombre": "Kliptium", "cantidad": 5},
        ],
    },
    {
        "id": "escudo_mk2",
        "nombre": "Escudo de plasma MK2",
        "categoria": "Defensa",
        "descripcion": "Refuerza el sistema defensivo de la nave.",
        "efecto": "Escudo máximo +25",
        "maximo": 225,
        "stat": "shield_max",
        "materiales": [
            {"resource_id": RESOURCE_IDS["Copper"], "nombre": "Copper", "cantidad": 10},
            {"resource_id": RESOURCE_IDS["Kliptium"], "nombre": "Kliptium", "cantidad": 10},
        ],
    },
    {
        "id": "blindaje_mk2",
        "nombre": "Blindaje reforzado MK2",
        "categoria": "Defensa",
        "descripcion": "Aumenta la resistencia estructural del casco.",
        "efecto": "Casco máximo +100",
        "maximo": 1000,
        "stat": "hull_max",
        "materiales": [
            {"resource_id": RESOURCE_IDS["Copper"], "nombre": "Copper", "cantidad": 10},
            {"resource_id": RESOURCE_IDS["Material Orgánico"], "nombre": "Material Orgánico", "cantidad": 8},
            {"resource_id": RESOURCE_IDS["Kliptium"], "nombre": "Kliptium", "cantidad": 5},
        ],
    },
    {
        "id": "extractor_mk2",
        "nombre": "Extractor minero MK2",
        "categoria": "Minería",
        "descripcion": "Mejora el módulo de extracción para futuras operaciones mineras.",
        "efecto": "Nivel de extractor +1",
        "maximo": 5,
        "stat": "extractor_level",
        "materiales": [
            {"resource_id": RESOURCE_IDS["Kliptium"], "nombre": "Kliptium", "cantidad": 15},
            {"resource_id": RESOURCE_IDS["Litium"], "nombre": "Litium", "cantidad": 10},
        ],
    },
    {
        "id": "bodega_mk2",
        "nombre": "Bodega expandida MK2",
        "categoria": "Carga",
        "descripcion": "Aumenta la capacidad de carga disponible para operaciones futuras.",
        "efecto": "Capacidad de carga +250",
        "maximo": 2500,
        "stat": "cargo_capacity",
        "materiales": [
            {"resource_id": RESOURCE_IDS["Copper"], "nombre": "Copper", "cantidad": 8},
            {"resource_id": RESOURCE_IDS["Kliptium"], "nombre": "Kliptium", "cantidad": 8},
            {"resource_id": RESOURCE_IDS["H2O"], "nombre": "H2O", "cantidad": 5},
        ],
    },
]


STAT_LABELS = {
    "energy_max": "Energía máxima",
    "shield_max": "Escudo máximo",
    "hull_max": "Casco máximo",
    "extractor_level": "Nivel de extractor",
    "cargo_capacity": "Capacidad de carga",
}


UPGRADE_VALUES = {
    "energy_max": 25,
    "shield_max": 25,
    "hull_max": 100,
    "extractor_level": 1,
    "cargo_capacity": 250,
}


def _get_player_id(current_user: User) -> int:
    if current_user.jugador is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un jugador asociado a este usuario.",
        )

    return int(current_user.jugador.id)


def _inventory_map(db: Session, player_id: int) -> dict[int, int]:
    rows = (
        db.query(Inventory)
        .filter(Inventory.player_id == player_id)
        .all()
    )

    return {
        int(row.resource_id): int(row.quantity or 0)
        for row in rows
    }


def _recipe_by_id(recipe_id: str) -> dict:
    for recipe in BASE_RECIPES:
        if recipe["id"] == recipe_id:
            return recipe

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Receta no encontrada.",
    )


def _ship_payload(ship: Ship) -> dict:
    return {
        "nombre": str(ship.name),
        "nivel": int(ship.level or 1),
        "energia_actual": int(ship.energy_current or 0),
        "energia_maxima": int(ship.energy_max or 0),
        "escudo_actual": int(ship.shield_current or 0),
        "escudo_maximo": int(ship.shield_max or 0),
        "casco_actual": int(ship.hull_current or 0),
        "casco_maximo": int(ship.hull_max or 0),
        "capacidad_carga": int(ship.cargo_capacity or 0),
        "nivel_extractor": int(ship.extractor_level or 1),
        "ranuras_armas": int(ship.weapon_slots or 0),
        "ranuras_tripulacion": int(ship.crew_slots or 0),
    }


def _decorate_recipe(recipe: dict, inventory: dict[int, int], ship: Ship) -> dict:
    stat = str(recipe["stat"])
    current_value = int(getattr(ship, stat) or 0)
    max_value = int(recipe["maximo"])
    max_reached = current_value >= max_value

    materials = []
    missing = []

    for material in recipe["materiales"]:
        resource_id = int(material["resource_id"])
        required = int(material["cantidad"])
        available = int(inventory.get(resource_id, 0))
        enough = available >= required

        materials.append({
            "resource_id": resource_id,
            "nombre": material["nombre"],
            "cantidad": required,
            "disponible": available,
            "suficiente": enough,
        })

        if not enough:
            missing.append({
                "resource_id": resource_id,
                "nombre": material["nombre"],
                "faltan": required - available,
            })

    can_craft = (not max_reached) and len(missing) == 0

    return {
        "id": recipe["id"],
        "nombre": recipe["nombre"],
        "categoria": recipe["categoria"],
        "descripcion": recipe["descripcion"],
        "efecto": recipe["efecto"],
        "stat": stat,
        "stat_nombre": STAT_LABELS.get(stat, stat),
        "valor_actual": current_value,
        "valor_maximo": max_value,
        "maximo_alcanzado": max_reached,
        "materiales": materials,
        "faltantes": missing,
        "puede_fabricar": can_craft,
    }


def _consume_materials(db: Session, player_id: int, recipe: dict) -> None:
    for material in recipe["materiales"]:
        resource_id = int(material["resource_id"])
        required = int(material["cantidad"])

        row = (
            db.query(Inventory)
            .filter(
                Inventory.player_id == player_id,
                Inventory.resource_id == resource_id,
            )
            .with_for_update()
            .first()
        )

        if row is None or int(row.quantity or 0) < required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No tienes suficientes materiales para fabricar esta mejora.",
            )

        row.quantity = int(row.quantity or 0) - required


def _apply_upgrade(ship: Ship, recipe: dict) -> dict:
    stat = str(recipe["stat"])
    current_value = int(getattr(ship, stat) or 0)
    max_value = int(recipe["maximo"])

    if current_value >= max_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta mejora ya alcanzó su nivel máximo.",
        )

    increase = int(UPGRADE_VALUES[stat])
    new_value = min(current_value + increase, max_value)
    setattr(ship, stat, new_value)

    if stat == "energy_max":
        ship.energy_current = min(int(ship.energy_current or 0) + increase, int(ship.energy_max or 0))

    if stat == "shield_max":
        ship.shield_current = min(int(ship.shield_current or 0) + increase, int(ship.shield_max or 0))

    if stat == "hull_max":
        ship.hull_current = min(int(ship.hull_current or 0) + increase, int(ship.hull_max or 0))

    if stat in {"energy_max", "shield_max", "hull_max", "extractor_level", "cargo_capacity"}:
        ship.level = int(ship.level or 1) + 1

    return {
        "stat": stat,
        "stat_nombre": STAT_LABELS.get(stat, stat),
        "valor_anterior": current_value,
        "valor_nuevo": new_value,
        "incremento": new_value - current_value,
    }


@router.get(
    "/recetas",
    status_code=status.HTTP_200_OK,
    name="Ver recetas de fabricación y mejoras",
)
def listar_recetas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    player_id = _get_player_id(current_user)
    ship = get_or_create_ship(db=db, user=current_user)
    inventory = _inventory_map(db=db, player_id=player_id)

    recipes = [
        _decorate_recipe(
            recipe=recipe,
            inventory=inventory,
            ship=ship,
        )
        for recipe in BASE_RECIPES
    ]

    return {
        "comandante": current_user.username,
        "nave": _ship_payload(ship),
        "recetas": recipes,
    }


@router.post(
    "/fabricar",
    status_code=status.HTTP_200_OK,
    name="Fabricar mejora de nave",
)
def fabricar_mejora(
    receta_id: str = Query(..., description="ID de la receta a fabricar."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    player_id = _get_player_id(current_user)
    recipe = _recipe_by_id(receta_id)
    ship = get_or_create_ship(db=db, user=current_user)
    inventory = _inventory_map(db=db, player_id=player_id)
    decorated_recipe = _decorate_recipe(
        recipe=recipe,
        inventory=inventory,
        ship=ship,
    )

    if not bool(decorated_recipe["puede_fabricar"]):
        if bool(decorated_recipe["maximo_alcanzado"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta mejora ya llegó al máximo permitido.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tienes suficientes materiales para fabricar esta mejora.",
        )

    try:
        _consume_materials(
            db=db,
            player_id=player_id,
            recipe=recipe,
        )

        result = _apply_upgrade(
            ship=ship,
            recipe=recipe,
        )

        db.commit()
        db.refresh(ship)

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible fabricar la mejora: " + str(error),
        ) from error

    return {
        "status": "success",
        "mensaje": "Mejora fabricada correctamente: " + str(recipe["nombre"]),
        "receta_id": receta_id,
        "resultado": result,
        "nave": _ship_payload(ship),
    }
