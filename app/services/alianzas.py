# app/services/alianzas.py
from sqlalchemy.orm import Session
from app.models.alianzas import Alliance
from app.models.user import User
from app.schemas.alianzas import AlianzaCrearPeticion

def get_alliances(db: Session, search: str | None = None):
    query = db.query(Alliance)
    if search:
        query = query.filter(Alliance.name.ilike(f"%{search}%"))
    return query.all()


def create_alliance(db: Session, alliance_data: AlianzaCrearPeticion, current_user: User):
    # 1. Validación: Verificar que el nombre de la alianza no esté tomado
    existing_alliance = db.query(Alliance).filter(Alliance.name.ilike(alliance_data.nombre)).first()
    if existing_alliance:
        raise ValueError("El nombre de la alianza ya está registrado por otra corporación.")

    # 2. Validación: Verificar que el tag no esté repetido
    existing_tag = db.query(Alliance).filter(Alliance.tag.ilike(alliance_data.tag)).first()
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