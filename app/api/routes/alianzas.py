# app/api/routes/alianzas.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.schemas.alianzas import AlianzaCrearPeticion, AlianzaRespuesta
from app.services import alianzas as alianzas_service

# 🌟 IMPORTAMOS EL SEGURIDAD Y EL MODELO DE USUARIO
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/alianzas", tags=["Alianzas"])


@router.post("/crear", response_model=AlianzaRespuesta, status_code=status.HTTP_201_CREATED, name="Crear Alianza")
def crear_alianza(
    payload: AlianzaCrearPeticion, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # 🌟 Exige token JWT obligatorio
):
    """
    Registra una nueva alianza en el universo de Galactum.
    Solo permitido para comandantes autenticados que no pertenezcan a otra alianza.
    """
    try:
        # Pasamos el usuario actual al servicio para saber quién es el fundador
        nueva_alianza = alianzas_service.create_alliance(db, payload, current_user)
        return nueva_alianza
    except ValueError as ve:
        # Captura errores de lógica de negocio (ej: ya tiene alianza o nombre repetido)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear la alianza: {str(e)}"
        )


@router.get("/buscar", response_model=list[AlianzaRespuesta], name="Buscar Alianzas")
def buscar_alianzas(search: str | None = None, db: Session = Depends(get_db)):
    """
    Retorna la lista de alianzas. Este endpoint sigue siendo público 
    para que los jugadores puedan buscar clanes desde el menú principal.
    """
    try:
        alianzas = alianzas_service.get_alliances(db, search=search)
        return alianzas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al buscar alianzas: {str(e)}"
        )
@router.get("/mi-alianza", response_model=AlianzaRespuesta | None, name="Ver mi Alianza")
def ver_mi_alianza(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🌟 EXTRA URGENTE PARA LA DEMO: Devuelve la alianza a la que pertenece 
    el jugador autenticado. Si no tiene alianza, devuelve null.
    Perfecto para que Godot cargue el menú directo del clan.
    """
    try:
        if not current_user.jugador or not hasattr(current_user.jugador, 'alliance_id'):
            return None
            
        alliance_id = current_user.jugador.alliance_id
        if not alliance_id:
            return None
            
        alianza = db.query(Alliance).filter(Alliance.id == alliance_id).first()
        return alianza
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener tu alianza: {str(e)}"
        )