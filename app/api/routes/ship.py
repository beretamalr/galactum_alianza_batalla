from fastapi import APIRouter, Depends, status

from app.models.user import User
from app.services.auth import get_current_user


router = APIRouter(
    prefix="/ship",
    tags=["Nave"],
)


@router.get(
    "/estado",
    status_code=status.HTTP_200_OK,
    name="Ver Estado de la Nave",
)
def ver_estado_nave(
    current_user: User = Depends(get_current_user),
):
    """
    Entrega información temporal de la nave del usuario autenticado.

    Esta versión todavía no consulta la tabla ships. Sirve para comprobar
    el flujo completo Godot -> FastAPI -> Godot antes de implementar
    persistencia real en PostgreSQL.
    """

    return {
        "comandante": current_user.username,
        "nave": {
            "nombre": "Galactum Explorer",
            "nivel": 1,
            "energia_actual": 50,
            "energia_maxima": 50,
            "escudo_actual": 100,
            "escudo_maximo": 100,
            "casco_actual": 500,
            "casco_maximo": 500,
            "posicion": {
                "x": 0,
                "y": 0,
            },
            "velocidad": 100,
            "en_movimiento": False,
            "mejoras_disponibles": True,
        },
    }
