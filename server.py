from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.v2_features_beta.models.server import Server # type: ignore
from app.v2_features_beta.schemas.server import ServerCreate, ServerUpdate # type: ignore

# Crear servidor
def register_server(db: Session, owner_id: UUID, data: ServerCreate) -> Server:
    srv = Server(name=data.name, region=data.region, owner_id=owner_id)
    db.add(srv)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Se propagará al controlador para devolver 409
        raise
    db.refresh(srv)
    return srv

# Listar los servidores del owner
def get_user_servers(db: Session, owner_id: UUID) -> List[Server]:
    return list(db.execute(select(Server).where(Server.owner_id == owner_id)).scalars().all())

# Obtener por id
def get_server_by_id(db: Session, server_id: UUID) -> Optional[Server]:
    return db.get(Server, server_id)

# Actualizar (name/region)
def update_server(db: Session, srv: Server, data: ServerUpdate) -> Server:
    if data.name is not None:
        srv.name = data.name
    if data.region is not None:
        srv.region = data.region

    db.add(srv)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Se propagará al controlador para devolver 409
        raise
    db.refresh(srv)
    return srv

# Eliminar
def delete_server(db: Session, srv: Server) -> None:
    db.delete(srv)
    db.commit()