from datetime import datetime

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.alianzas import Alliance, AllianceJoinRequest
from app.models.jugador import Jugador
from app.models.user import User
from app.schemas.alianzas import AlianzaCrearPeticion, SolicitudCrearPeticion


OFFICIAL_ALLIANCES = [
    {"name": "Legión Aurora", "tag": "AURA", "level": 9, "members_count": 64, "max_members": 150, "power": "18450", "lang": "ES", "puntos_prestigio": 14200, "required_power": 0},
    {"name": "Nova Orion", "tag": "NOVA", "level": 7, "members_count": 42, "max_members": 100, "power": "12850", "lang": "ES", "puntos_prestigio": 9800, "required_power": 0},
    {"name": "Cobalt Union", "tag": "CBLT", "level": 4, "members_count": 18, "max_members": 80, "power": "6420", "lang": "ES", "puntos_prestigio": 3100, "required_power": 0},
    {"name": "Sideral Forge", "tag": "FORG", "level": 5, "members_count": 26, "max_members": 90, "power": "8910", "lang": "ES", "puntos_prestigio": 4700, "required_power": 0},
    {"name": "Eclipse Vanguard", "tag": "ECLP", "level": 6, "members_count": 31, "max_members": 120, "power": "10420", "lang": "ES", "puntos_prestigio": 6100, "required_power": 0},
    {"name": "Helios Pact", "tag": "HELI", "level": 3, "members_count": 12, "max_members": 60, "power": "3880", "lang": "ES", "puntos_prestigio": 1900, "required_power": 0},
    {"name": "Iron Nebula", "tag": "IRON", "level": 8, "members_count": 54, "max_members": 150, "power": "15900", "lang": "ES", "puntos_prestigio": 12100, "required_power": 0},
    {"name": "Solaris Core", "tag": "SOLR", "level": 2, "members_count": 9, "max_members": 50, "power": "2240", "lang": "ES", "puntos_prestigio": 760, "required_power": 0},
]


def _get_player(current_user: User) -> Jugador:
    if not current_user.jugador:
        raise ValueError("El usuario autenticado no tiene un jugador asociado.")
    return current_user.jugador


def _get_alliance_or_raise(db: Session, alliance_id: int) -> Alliance:
    alliance = db.query(Alliance).filter(Alliance.id == alliance_id).first()
    if not alliance:
        raise ValueError("La alianza no existe.")
    return alliance


def _get_leader_alliance_or_raise(db: Session, current_user: User) -> tuple[Jugador, Alliance]:
    player = _get_player(current_user)

    if player.alliance_id is None:
        raise ValueError("No perteneces a una alianza.")

    alliance = _get_alliance_or_raise(db, player.alliance_id)

    if alliance.leader_jugador_id != player.id:
        raise ValueError("Solo el líder de la alianza puede realizar esta acción.")

    return player, alliance


def _member_payload(player: Jugador, alliance: Alliance) -> dict:
    return {
        "jugador_id": player.id,
        "nombre": player.nickname,
        "poder": player.power or 0,
        "es_lider": alliance.leader_jugador_id == player.id,
    }


def _request_payload(request: AllianceJoinRequest, alliance: Alliance) -> dict:
    return {
        "id": request.id,
        "alianza_id": request.alliance_id,
        "estado": request.status,
        "mensaje": request.message,
        "creada_en": request.created_at,
        "solicitante": _member_payload(request.applicant, alliance),
    }


def ensure_official_alliances(db: Session):
    created = False

    for alliance_data in OFFICIAL_ALLIANCES:
        existing_alliance = db.query(Alliance).filter(
            Alliance.name == alliance_data["name"],
            Alliance.tag == alliance_data["tag"],
        ).first()

        if not existing_alliance:
            db.add(Alliance(**alliance_data))
            created = True

    if created:
        db.commit()


def get_alliances(db: Session, search: str | None = None):
    ensure_official_alliances(db)
    query = db.query(Alliance)
    term = (search or "").strip()

    if term:
        pattern = f"%{term}%"
        query = query.filter(or_(Alliance.name.ilike(pattern), Alliance.tag.ilike(pattern)))

    return query.order_by(Alliance.level.desc(), Alliance.members_count.desc()).all()


def get_alliance_detail(db: Session, alliance_id: int) -> dict:
    alliance = _get_alliance_or_raise(db, alliance_id)
    members = (
        db.query(Jugador)
        .filter(Jugador.alliance_id == alliance.id)
        .order_by(Jugador.power.desc(), Jugador.nickname.asc())
        .all()
    )

    return {
        "id": alliance.id,
        "nombre": alliance.name,
        "tag": alliance.tag,
        "nivel": alliance.level,
        "miembros_actuales": alliance.members_count,
        "miembros_maximos": alliance.max_members,
        "poder_total": alliance.power,
        "region": alliance.lang,
        "req_poder": alliance.required_power,
        "puntos_prestigio": alliance.puntos_prestigio,
        "lider_jugador_id": alliance.leader_jugador_id,
        "miembros": [_member_payload(member, alliance) for member in members],
    }


def create_alliance(db: Session, alliance_data: AlianzaCrearPeticion, current_user: User):
    player = _get_player(current_user)

    if player.alliance_id is not None:
        raise ValueError("Ya perteneces a una alianza. Debes abandonarla antes de fundar una nueva.")

    normalized_name = alliance_data.nombre.strip()
    normalized_tag = alliance_data.tag.strip().upper()

    existing_name = db.query(Alliance).filter(func.lower(Alliance.name) == normalized_name.lower()).first()
    if existing_name:
        raise ValueError("El nombre de la alianza ya está registrado.")

    existing_tag = db.query(Alliance).filter(func.lower(Alliance.tag) == normalized_tag.lower()).first()
    if existing_tag:
        raise ValueError("El TAG de la alianza ya está siendo usado.")

    try:
        alliance = Alliance(
            name=normalized_name,
            tag=normalized_tag,
            level=1,
            members_count=1,
            max_members=100,
            power=str(player.power or 0),
            lang="ES",
            puntos_prestigio=0,
            required_power=alliance_data.req_poder,
        )
        db.add(alliance)
        db.flush()

        player.alliance_id = alliance.id
        alliance.leader_jugador_id = player.id

        db.commit()
        db.refresh(alliance)
        return alliance
    except Exception:
        db.rollback()
        raise


def create_join_request(
    db: Session,
    alliance_id: int,
    payload: SolicitudCrearPeticion,
    current_user: User,
) -> dict:
    player = _get_player(current_user)
    alliance = _get_alliance_or_raise(db, alliance_id)

    if player.alliance_id is not None:
        raise ValueError("Ya perteneces a una alianza. No puedes enviar una solicitud nueva.")

    if alliance.leader_jugador_id is None:
        raise ValueError("Esta alianza no tiene un líder configurado para revisar solicitudes.")

    if player.power < alliance.required_power:
        raise ValueError(
            f"Poder insuficiente. Se requieren {alliance.required_power} y tienes {player.power}."
        )

    if alliance.members_count >= alliance.max_members:
        raise ValueError("La alianza está completa.")

    existing_pending = (
        db.query(AllianceJoinRequest)
        .filter(
            AllianceJoinRequest.alliance_id == alliance.id,
            AllianceJoinRequest.applicant_jugador_id == player.id,
            AllianceJoinRequest.status == "pending",
        )
        .first()
    )
    if existing_pending:
        raise ValueError("Ya tienes una solicitud pendiente para esta alianza.")

    try:
        request = AllianceJoinRequest(
            alliance_id=alliance.id,
            applicant_jugador_id=player.id,
            message=payload.mensaje.strip() or None,
            status="pending",
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        return _request_payload(request, alliance)
    except Exception:
        db.rollback()
        raise


def get_pending_requests(db: Session, current_user: User) -> list[dict]:
    _, alliance = _get_leader_alliance_or_raise(db, current_user)
    requests = (
        db.query(AllianceJoinRequest)
        .filter(
            AllianceJoinRequest.alliance_id == alliance.id,
            AllianceJoinRequest.status == "pending",
        )
        .order_by(AllianceJoinRequest.created_at.asc())
        .all()
    )
    return [_request_payload(request, alliance) for request in requests]


def accept_join_request(db: Session, request_id: int, current_user: User) -> dict:
    leader, alliance = _get_leader_alliance_or_raise(db, current_user)
    request = db.query(AllianceJoinRequest).filter(AllianceJoinRequest.id == request_id).first()

    if not request or request.alliance_id != alliance.id:
        raise ValueError("La solicitud no existe o no pertenece a tu alianza.")

    if request.status != "pending":
        raise ValueError("La solicitud ya fue procesada.")

    applicant = request.applicant
    if applicant.alliance_id is not None:
        raise ValueError("El solicitante ya pertenece a una alianza.")

    if applicant.power < alliance.required_power:
        raise ValueError("El solicitante ya no cumple el requisito de poder.")

    if alliance.members_count >= alliance.max_members:
        raise ValueError("La alianza está completa.")

    try:
        applicant.alliance_id = alliance.id
        alliance.members_count += 1
        request.status = "accepted"
        request.reviewed_by_jugador_id = leader.id
        request.reviewed_at = datetime.utcnow()

        # El jugador no puede tener solicitudes pendientes en otras alianzas al ser aceptado.
        (
            db.query(AllianceJoinRequest)
            .filter(
                AllianceJoinRequest.applicant_jugador_id == applicant.id,
                AllianceJoinRequest.status == "pending",
                AllianceJoinRequest.id != request.id,
            )
            .update(
                {"status": "cancelled", "reviewed_by_jugador_id": leader.id, "reviewed_at": datetime.utcnow()},
                synchronize_session=False,
            )
        )

        db.commit()
        return {"mensaje": f"Solicitud aceptada. {applicant.nickname} ya pertenece a {alliance.name}."}
    except Exception:
        db.rollback()
        raise


def reject_join_request(db: Session, request_id: int, current_user: User) -> dict:
    leader, alliance = _get_leader_alliance_or_raise(db, current_user)
    request = db.query(AllianceJoinRequest).filter(AllianceJoinRequest.id == request_id).first()

    if not request or request.alliance_id != alliance.id:
        raise ValueError("La solicitud no existe o no pertenece a tu alianza.")

    if request.status != "pending":
        raise ValueError("La solicitud ya fue procesada.")

    try:
        request.status = "rejected"
        request.reviewed_by_jugador_id = leader.id
        request.reviewed_at = datetime.utcnow()
        db.commit()
        return {"mensaje": "Solicitud rechazada."}
    except Exception:
        db.rollback()
        raise


def kick_member(db: Session, jugador_id: int, current_user: User) -> dict:
    _, alliance = _get_leader_alliance_or_raise(db, current_user)

    if jugador_id == alliance.leader_jugador_id:
        raise ValueError("El líder no puede expulsarse a sí mismo.")

    member = (
        db.query(Jugador)
        .filter(Jugador.id == jugador_id, Jugador.alliance_id == alliance.id)
        .first()
    )
    if not member:
        raise ValueError("El jugador no pertenece a tu alianza.")

    try:
        member.alliance_id = None
        alliance.members_count = max(1, alliance.members_count - 1)
        db.commit()
        return {"mensaje": f"{member.nickname} fue expulsado de la alianza."}
    except Exception:
        db.rollback()
        raise
