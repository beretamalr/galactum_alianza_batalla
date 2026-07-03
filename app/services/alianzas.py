# app/services/alianzas.py
from sqlalchemy.orm import Session
from app.models.alianzas import Alliance
from app.models.user import User
from app.schemas.alianzas import AlianzaCrearPeticion

OFFICIAL_ALLIANCES = [
    {
        "name": "Legión Aurora",
        "tag": "AURA",
        "level": 9,
        "members_count": 64,
        "max_members": 150,
        "power": "18450",
        "lang": "ES",
        "puntos_prestigio": 14200,
    },
    {
        "name": "Nova Orion",
        "tag": "NOVA",
        "level": 7,
        "members_count": 42,
        "max_members": 100,
        "power": "12850",
        "lang": "ES",
        "puntos_prestigio": 9800,
    },
    {
        "name": "Cobalt Union",
        "tag": "CBLT",
        "level": 4,
        "members_count": 18,
        "max_members": 80,
        "power": "6420",
        "lang": "ES",
        "puntos_prestigio": 3100,
    },
    {
        "name": "Sideral Forge",
        "tag": "FORG",
        "level": 5,
        "members_count": 26,
        "max_members": 90,
        "power": "8910",
        "lang": "ES",
        "puntos_prestigio": 4700,
    },
    {
        "name": "Eclipse Vanguard",
        "tag": "ECLP",
        "level": 6,
        "members_count": 31,
        "max_members": 120,
        "power": "10420",
        "lang": "ES",
        "puntos_prestigio": 6100,
    },
    {
        "name": "Helios Pact",
        "tag": "HELI",
        "level": 3,
        "members_count": 12,
        "max_members": 60,
        "power": "3880",
        "lang": "ES",
        "puntos_prestigio": 1900,
    },
    {
        "name": "Iron Nebula",
        "tag": "IRON",
        "level": 8,
        "members_count": 54,
        "max_members": 150,
        "power": "15900",
        "lang": "ES",
        "puntos_prestigio": 12100,
    },
    {
        "name": "Solaris Core",
        "tag": "SOLR",
        "level": 2,
        "members_count": 9,
        "max_members": 50,
        "power": "2240",
        "lang": "ES",
        "puntos_prestigio": 760,
    }
]


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
    if search:
        query = query.filter(Alliance.name.ilike(f"%{search}%"))
    return query.all()


def create_alliance(db: Session, alliance_data: AlianzaCrearPeticion, current_user: User):
    # 1. Validación: Verificar que el nombre de la alianza no esté tomado
    existing_alliance = db.query(Alliance).filter(Alliance.name.ilike(f"%{alliance_data.nombre}%")).first()
    if existing_alliance:
        raise ValueError("El nombre de la alianza ya está registrado por otra corporación.")

    # 2. Validación: Verificar que el tag no esté repetido
    existing_tag = db.query(Alliance).filter(Alliance.tag.ilike(f"%{alliance_data.tag}%")).first()
    if existing_tag:
        raise ValueError("El TAG de la alianza ya está siendo usado.")

    # 3. Crear la entidad de la Alianza
    db_alliance = Alliance(
        name=alliance_data.nombre,
        tag=alliance_data.tag,
        level=1,
        members_count=1,
        max_members=100,
        power="0",
        lang="ES",
        puntos_prestigio=0
    )
    
    try:
        db.add(db_alliance)
        db.flush()  # Genera el ID de la alianza en la base de datos
        
        # 4. Vincular al jugador como miembro/líder si tu modelo Jugador tiene la columna alliance_id
        if current_user.jugador and hasattr(current_user.jugador, 'alliance_id'):
            # Si ya pertenecía a una alianza, lanzar error
            if current_user.jugador.alliance_id is not None:
                raise ValueError("Ya perteneces a una alianza. Debes abandonarla antes de fundar una nueva.")
            
            current_user.jugador.alliance_id = db_alliance.id

        db.commit()
        db.refresh(db_alliance)
        return db_alliance

    except Exception as e:
        db.rollback()
        raise e


def join_alliance(db: Session, alliance_id: int, current_user: User):
    if not current_user.jugador:
        raise ValueError("El usuario no tiene un jugador asociado.")

    alliance = db.query(Alliance).filter(Alliance.id == alliance_id).first()
    if not alliance:
        raise ValueError("La alianza no existe.")

    if current_user.jugador.alliance_id is not None:
        if current_user.jugador.alliance_id == alliance_id:
            return alliance
        raise ValueError("Ya perteneces a una alianza. Debes abandonarla antes de unirte a otra.")

    alliance.members_count = (alliance.members_count or 0) + 1
    current_user.jugador.alliance_id = alliance.id
    db.commit()
    db.refresh(alliance)
    return alliance