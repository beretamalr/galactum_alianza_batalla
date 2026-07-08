# app/api/routes/map.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.ship import Position
from app.services.auth import get_current_user
from app.services.ship import get_or_create_ship, get_ship_state, start_player_move


router = APIRouter(
    prefix="/map",
    tags=["Mapa y Exploración"],
)


# Sectores estáticos de demostración.
# No requieren tabla nueva: la nave sí se lee y se actualiza en Neon.
SECTORES_GALACTICOS = [
    {
        "id": 1,
        "nombre": "Nova Prime",
        "tipo": "Planeta habitable",
        "x": 1200.0,
        "y": -800.0,
        "energia_requerida": 15,
        "peligro": "Bajo",
        "descripcion": "Sistema estable con actividad comercial moderada.",
    },
    {
        "id": 2,
        "nombre": "Estación Omega",
        "tipo": "Estación comercial",
        "x": -500.0,
        "y": 600.0,
        "energia_requerida": 10,
        "peligro": "Bajo",
        "descripcion": "Punto de intercambio y reabastecimiento de flota.",
    },
    {
        "id": 3,
        "nombre": "Cinturón Kliptium",
        "tipo": "Zona minera",
        "x": 2300.0,
        "y": 1600.0,
        "energia_requerida": 25,
        "peligro": "Medio",
        "descripcion": "Sector rico en minerales estratégicos y asteroides explotables.",
    },
    {
        "id": 4,
        "nombre": "Nebulosa Orión",
        "tipo": "Nebulosa",
        "x": -2100.0,
        "y": -1500.0,
        "energia_requerida": 30,
        "peligro": "Alto",
        "descripcion": "Zona de baja visibilidad con actividad hostil intermitente.",
    },
    {
        "id": 5,
        "nombre": "Abismo Violeta",
        "tipo": "Anomalía",
        "x": 3800.0,
        "y": -2600.0,
        "energia_requerida": 40,
        "peligro": "Crítico",
        "descripcion": "Anomalía espacial inestable. Requiere nave preparada.",
    },
]


def _buscar_sector(sector_id: int) -> dict | None:
    for sector in SECTORES_GALACTICOS:
        if int(sector["id"]) == int(sector_id):
            return sector
    return None


def _destino_actual(ship) -> dict | None:
    if ship.end_pos_x is None or ship.end_pos_y is None:
        return None

    return {
        "x": float(ship.end_pos_x),
        "y": float(ship.end_pos_y),
    }


@router.get(
    "/sectores",
    status_code=status.HTTP_200_OK,
    name="Obtener Mapa Galáctico",
)
def obtener_mapa_galactico(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el mapa visible para Godot.

    La lista de sectores es estática para la demo, pero la posición y estado
    de la nave se leen desde la tabla ships en Neon.
    """

    try:
        estado_nave = get_ship_state(
            db=db,
            user=current_user,
        )

        ship = get_or_create_ship(
            db=db,
            user=current_user,
        )

        nave = estado_nave["nave"]
        destino = _destino_actual(ship)

        return {
            "comandante": current_user.username,
            "nave": {
                "nombre": nave["nombre"],
                "energia_actual": nave["energia_actual"],
                "energia_maxima": nave["energia_maxima"],
                "posicion": nave["posicion"],
                "en_movimiento": nave["en_movimiento"],
                "velocidad": nave["velocidad"],
                "destino": destino,
            },
            "sectores": SECTORES_GALACTICOS,
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible obtener el mapa galáctico: " + str(error),
        )


@router.post(
    "/viajar",
    status_code=status.HTTP_200_OK,
    name="Viajar a un sector",
)
def viajar_a_sector(
    sector_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Inicia un viaje real de la nave hacia el sector seleccionado.

    Actualiza la tabla ships en Neon usando las columnas de movimiento:
    start_pos_x/y, end_pos_x/y, movement_start_time,
    estimated_arrival_time e is_moving.
    """

    sector = _buscar_sector(sector_id)

    if sector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sector galáctico no encontrado.",
        )

    try:
        ship = get_or_create_ship(
            db=db,
            user=current_user,
        )

        energia_requerida = int(sector.get("energia_requerida", 0))
        energia_actual = int(ship.energy_current or 0)

        if energia_actual < energia_requerida:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Energía insuficiente para viajar a "
                    + str(sector["nombre"])
                    + ". Energía requerida: "
                    + str(energia_requerida)
                    + ". Energía disponible: "
                    + str(energia_actual)
                    + "."
                ),
            )

        ship.energy_current = energia_actual - energia_requerida
        db.flush()

        viaje = start_player_move(
            db=db,
            user_id=current_user.id,
            target_pos=Position(
                x=float(sector["x"]),
                y=float(sector["y"]),
            ),
        )

        return {
            "status": "success",
            "mensaje": "Viaje iniciado hacia " + str(sector["nombre"]) + ".",
            "sector": sector,
            "energia_consumida": energia_requerida,
            "energia_restante": energia_actual - energia_requerida,
            "viaje": {
                "inicio": {
                    "x": viaje.startPosition.x,
                    "y": viaje.startPosition.y,
                },
                "destino": {
                    "x": viaje.endPosition.x,
                    "y": viaje.endPosition.y,
                },
                "fecha_inicio": viaje.movementStartTime.isoformat(),
                "fecha_llegada_estimada": viaje.estimatedArrivalTime.isoformat(),
            },
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible iniciar el viaje: " + str(error),
        )
