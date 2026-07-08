# app/api/routes/tripulantes.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.jugador import Jugador
from app.models.tripulante import Tripulante
from app.models.user import User
from app.services.auth import get_current_user


router = APIRouter(prefix="/tripulantes", tags=["Tripulantes"])


@router.get(
    "/mi-nave",
    status_code=status.HTTP_200_OK,
    name="Ver Tripulación Real de la Nave",
)
def ver_tripulacion(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve los tripulantes reales asociados al jugador autenticado.

    Si el jugador no tiene tripulantes, devuelve una lista vacía.
    Godot mostrará: "No se encontraron tripulantes en la nave".
    """
    jugador = _obtener_jugador_actual(
        db=db,
        current_user=current_user,
    )

    tripulantes = (
        db.query(Tripulante)
        .filter(Tripulante.player_id == jugador.id)
        .order_by(Tripulante.id.asc())
        .all()
    )

    return [_serializar_tripulante(tripulante) for tripulante in tripulantes]


@router.post(
    "/reclutar",
    status_code=status.HTTP_201_CREATED,
    name="Reclutar Tripulante Real",
)
def reclutar_tripulante(
    rol_deseado: str = Query(
        default="Ingeniero de Nave",
        min_length=3,
        description="Rol o especialización inicial del tripulante.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crea un tripulante real en Neon para el jugador autenticado.

    Este endpoint sirve para probar la pantalla desde Swagger/Postman sin
    insertar datos manualmente en Neon.
    """
    jugador = _obtener_jugador_actual(
        db=db,
        current_user=current_user,
    )

    total_tripulantes = (
        db.query(Tripulante)
        .filter(Tripulante.player_id == jugador.id)
        .count()
    )

    nombre_generado = _generar_nombre_tripulante(total_tripulantes + 1)

    nuevo_tripulante = Tripulante(
        player_id=jugador.id,
        nombre=nombre_generado,
        nivel=1,
        especializacion=rol_deseado,
        slot_id=None,
    )

    db.add(nuevo_tripulante)
    db.commit()
    db.refresh(nuevo_tripulante)

    return {
        "status": "success",
        "message": "Tripulante reclutado correctamente.",
        "tripulante": _serializar_tripulante(nuevo_tripulante),
    }


def _obtener_jugador_actual(
    db: Session,
    current_user: User,
) -> Jugador:
    jugador = (
        db.query(Jugador)
        .filter(Jugador.user_id == current_user.id)
        .first()
    )

    if jugador is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un jugador asociado al usuario autenticado.",
        )

    return jugador


def _serializar_tripulante(tripulante: Tripulante) -> dict:
    especializacion = tripulante.especializacion or "Sin especialización"
    slot_id = tripulante.slot_id

    estado = "Asignado" if slot_id is not None else "Disponible"

    return {
        "id": tripulante.id,
        "nombre": tripulante.nombre,
        "nivel": tripulante.nivel,
        "rol": especializacion,
        "especializacion": especializacion,
        "estado": estado,
        "slot_id": slot_id,
        "lore": _generar_lore(especializacion, estado),
        "stats": {
            "nivel": tripulante.nivel,
            "especializacion": especializacion,
            "estado": estado,
            "sala": slot_id if slot_id is not None else "Sin asignar",
        },
    }


def _generar_lore(
    especializacion: str,
    estado: str,
) -> str:
    especializacion_normalizada = especializacion.lower()

    if "ingeniero" in especializacion_normalizada:
        base = "Especialista en sistemas de propulsión, reparación y mantenimiento de nave."
    elif "escudo" in especializacion_normalizada:
        base = "Oficial entrenado en protección defensiva y administración de escudos."
    elif "piloto" in especializacion_normalizada:
        base = "Tripulante orientado a navegación, maniobras y rutas espaciales."
    elif "táctico" in especializacion_normalizada or "tactico" in especializacion_normalizada:
        base = "Operador táctico preparado para decisiones de combate y apoyo ofensivo."
    elif "médico" in especializacion_normalizada or "medico" in especializacion_normalizada:
        base = "Especialista en soporte vital y recuperación de tripulación."
    else:
        base = "Tripulante registrado en la nave del comandante."

    return f"{base} Estado actual: {estado}."


def _generar_nombre_tripulante(numero: int) -> str:
    nombres = [
        "Sora Jax",
        "Tariq Vance",
        "Lena Oris",
        "Kael Rhovan",
        "Aris Thorne",
        "Nira Vale",
        "Dax Solen",
    ]

    indice = (numero - 1) % len(nombres)
    ciclos = (numero - 1) // len(nombres)

    if ciclos == 0:
        return nombres[indice]

    return f"{nombres[indice]} {ciclos + 1}"
