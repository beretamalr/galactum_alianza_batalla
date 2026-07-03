# app/api/routes/misiones.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/misiones", tags=["Misiones"])

@router.get("/disponibles", status_code=status.HTTP_200_OK, name="Listar Misiones Disponibles")
def listar_misiones(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retorna las misiones espaciales activas en el tablero que el comandante
    puede aceptar para ganar reputación y recursos.
    """
    try:
        # Aquí puedes retornar misiones base desde tu base de datos.
        # Dejamos un mock estructurado por si necesitas mostrar datos de inmediato:
        misiones_mock = [
            {
                "id": 1,
                "titulo": "Contrabando en el Sector Alfa",
                "descripcion": "Lleva 50 unidades de Helio-3 sin ser detectado.",
                "recompensa_creditos": 1500,
                "dificultad": "Fácil"
            },
            {
                "id": 2,
                "titulo": "Defensa de la Estación Minera",
                "descripcion": "Repele la incursión de piratas espaciales en los anillos de Saturno.",
                "recompensa_creditos": 5000,
                "dificultad": "Media"
            }
        ]
        return misiones_mock
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar el tablero de misiones: {str(e)}"
        )


@router.post("/{mision_id}/aceptar", status_code=status.HTTP_200_OK, name="Aceptar Misión")
def aceptar_mision(mision_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Asigna una misión del tablero al inventario de misiones activas del Comandante logueado.
    """
    try:
        # Aquí conectarías con tu misiones_service para guardar la relación en la BD
        return {
            "status": "success",
            "message": f"Misión {mision_id} asignada correctamente al comandante {current_user.username}."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo aceptar la misión: {str(e)}"
        )