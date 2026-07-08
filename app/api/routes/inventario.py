"""Rutas de inventario persistente para Galactum."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.crafting import CatalogoItem
from app.models.inventory import Inventory
from app.models.jugador import Jugador
from app.models.user import User
from app.services.auth import get_current_user


router = APIRouter(prefix="/inventario", tags=["Inventario"])


UNIDADES_POR_RECURSO: dict[str, str] = {
    "kliptium": "cristales",
    "material orgánico": "unidades",
    "material organico": "unidades",
    "litium": "unidades",
    "litio": "unidades",
    "copper": "unidades",
    "cobre": "unidades",
    "h2o": "litros",
    "agua": "litros",
}


def _obtener_unidad(nombre_recurso: str) -> str:
    """Devuelve una unidad de presentación estable para Godot."""
    return UNIDADES_POR_RECURSO.get(nombre_recurso.strip().lower(), "unidades")


@router.get(
    "/materiales",
    status_code=status.HTTP_200_OK,
    name="Ver Inventario de Recursos",
)
def ver_inventario(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Devuelve la bodega REAL del jugador autenticado.

    Contrato conservado para Godot:
    {
      "comandante": "...",
      "bodega": [
        {"recurso": "...", "cantidad": 0, "unidad": "...", "descripcion": "..."}
      ]
    }
    """
    jugador = (
        db.query(Jugador)
        .filter(Jugador.user_id == current_user.id)
        .first()
    )

    if jugador is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un perfil de jugador para este usuario.",
        )

    filas = (
        db.query(Inventory, CatalogoItem)
        .outerjoin(
            CatalogoItem,
            CatalogoItem.id == Inventory.resource_id,
        )
        .filter(Inventory.player_id == jugador.id)
        .order_by(Inventory.resource_id.asc())
        .all()
    )

    bodega: list[dict[str, Any]] = []
    total_unidades = 0

    for inventario, catalogo in filas:
        cantidad = int(inventario.quantity or 0)
        total_unidades += cantidad

        if catalogo is None:
            nombre_recurso = f"Recurso #{inventario.resource_id}"
            descripcion = "Recurso registrado en inventario sin ficha de catálogo."
            tipo = "recurso"
            rareza = "desconocida"
        else:
            nombre_recurso = str(catalogo.nombre)
            descripcion = str(
                catalogo.descripcion
                or "Material almacenado en la bodega del comandante."
            )
            tipo = str(catalogo.tipo or "recurso")
            rareza = str(catalogo.rareza or "comun")

        bodega.append(
            {
                "resource_id": int(inventario.resource_id),
                "recurso": nombre_recurso,
                "cantidad": cantidad,
                "unidad": _obtener_unidad(nombre_recurso),
                "descripcion": descripcion,
                "tipo": tipo,
                "rareza": rareza,
            }
        )

    return {
        "comandante": current_user.username,
        "bodega": bodega,
        "total_tipos": len(bodega),
        "total_unidades": total_unidades,
    }
