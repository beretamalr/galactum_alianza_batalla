# app/api/routes/server.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.db.session import get_db
from app.models.user import User
from app.models.server import Server
from app.schemas.server import ServerCreate, ServerUpdate, ServerOut
from app.services.auth import get_current_user

router = APIRouter(tags=["servers"])


# Crear server
@router.post("/servers/register", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
def register_server(
    payload: ServerCreate,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    # nombre único (global)
    exists = db.execute(select(Server).where(Server.name == payload.name)).scalars().first()
    if exists:
        raise HTTPException(status_code=409, detail="Ya existe un server con ese nombre")

    srv = Server(name=payload.name, region=payload.region, owner_id=me.id)
    db.add(srv)
    db.commit()
    db.refresh(srv)
    return srv


# Listar SÓLO mis servers
@router.get("/servers/my", response_model=list[ServerOut])
def my_servers(
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    rows = db.execute(select(Server).where(Server.owner_id == me.id).order_by(Server.created_at.desc())).scalars().all()
    return [
        s for s in rows
    ]


# Obtener un server por ID (si es mío)
@router.get("/servers/{server_id}", response_model=ServerOut)
def get_server_by_id(
    server_id: UUID,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    srv = db.execute(
        select(Server).where(and_(Server.id == server_id, Server.owner_id == me.id))
    ).scalars().first()

    if not srv:
        # No existe o no es tuyo → 404 (para no filtrar info de otros dueños)
        raise HTTPException(status_code=404, detail="Server no encontrado")

    return srv


# Actualizar (sólo si es mío)
@router.put("/servers/{server_id}", response_model=ServerOut)
def update_server(
    server_id: UUID,
    payload: ServerUpdate,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    srv = db.execute(
        select(Server).where(and_(Server.id == server_id, Server.owner_id == me.id))
    ).scalars().first()

    if not srv:
        raise HTTPException(status_code=404, detail="Server no encontrado")

    # Si cambia el nombre, volvemos a validar unicidad global
    if payload.name and payload.name != srv.name:
        conflict = db.execute(select(Server).where(Server.name == payload.name)).scalars().first()
        if conflict:
            raise HTTPException(status_code=409, detail="Ya existe un server con ese nombre")
        srv.name = payload.name # type: ignore

    if payload.region:
        srv.region = payload.region # type: ignore

    db.commit()
    db.refresh(srv)

    return srv


# Eliminar (sólo si es mío)
@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(
    server_id: UUID,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    srv = db.execute(
        select(Server).where(and_(Server.id == server_id, Server.owner_id == me.id))
    ).scalars().first()

    if not srv:
        raise HTTPException(status_code=404, detail="Server no encontrado")

    db.delete(srv)
    db.commit()
    return None
