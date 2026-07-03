from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.alianzas import (
    AlianzaCrearPeticion,
    AlianzaDetalleRespuesta,
    AlianzaRespuesta,
    OperacionRespuesta,
    SolicitudAlianzaRespuesta,
    SolicitudCrearPeticion,
)
from app.services import alianzas as alianzas_service
from app.services.auth import get_current_user

router = APIRouter(prefix="/alianzas", tags=["Alianzas"])


def _business_error(error: ValueError):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/buscar", response_model=list[AlianzaRespuesta], name="Buscar alianzas")
def buscar_alianzas(search: str | None = None, db: Session = Depends(get_db)):
    try:
        return alianzas_service.get_alliances(db, search=search)
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error))


@router.get("/mi-alianza", response_model=AlianzaRespuesta | None, name="Ver mi alianza")
def ver_mi_alianza(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        player = current_user.jugador
        if not player or player.alliance_id is None:
            return None
        return alianzas_service._get_alliance_or_raise(db, player.alliance_id)
    except ValueError as error:
        _business_error(error)


@router.get(
    "/mi-alianza/solicitudes",
    response_model=list[SolicitudAlianzaRespuesta],
    name="Solicitudes pendientes de mi alianza",
)
def listar_solicitudes_pendientes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return alianzas_service.get_pending_requests(db, current_user)
    except ValueError as error:
        _business_error(error)


@router.post("/crear", response_model=AlianzaRespuesta, status_code=status.HTTP_201_CREATED, name="Crear alianza")
def crear_alianza(
    payload: AlianzaCrearPeticion,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return alianzas_service.create_alliance(db, payload, current_user)
    except ValueError as error:
        _business_error(error)


@router.get("/{alliance_id}", response_model=AlianzaDetalleRespuesta, name="Detalle de alianza")
def obtener_detalle_alianza(alliance_id: int, db: Session = Depends(get_db)):
    try:
        return alianzas_service.get_alliance_detail(db, alliance_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.post(
    "/{alliance_id}/solicitudes",
    response_model=SolicitudAlianzaRespuesta,
    status_code=status.HTTP_201_CREATED,
    name="Enviar solicitud de ingreso",
)
def enviar_solicitud_ingreso(
    alliance_id: int,
    payload: SolicitudCrearPeticion,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return alianzas_service.create_join_request(db, alliance_id, payload, current_user)
    except ValueError as error:
        _business_error(error)


@router.post(
    "/solicitudes/{request_id}/aceptar",
    response_model=OperacionRespuesta,
    name="Aceptar solicitud",
)
def aceptar_solicitud(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return alianzas_service.accept_join_request(db, request_id, current_user)
    except ValueError as error:
        _business_error(error)


@router.post(
    "/solicitudes/{request_id}/rechazar",
    response_model=OperacionRespuesta,
    name="Rechazar solicitud",
)
def rechazar_solicitud(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return alianzas_service.reject_join_request(db, request_id, current_user)
    except ValueError as error:
        _business_error(error)


@router.delete(
    "/mi-alianza/miembros/{jugador_id}",
    response_model=OperacionRespuesta,
    name="Expulsar miembro",
)
def expulsar_miembro(
    jugador_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return alianzas_service.kick_member(db, jugador_id, current_user)
    except ValueError as error:
        _business_error(error)
