from datetime import datetime, timedelta, timezone

from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.dependencies import get_db
from app.models.jugador import Jugador
from app.models.user import User
from app.schemas.user import UserCreate

from app.services import inventory_service
from app.services import ship_rooms_service
from app.services.ship import create_initial_ship


settings = get_settings()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Genera el hash seguro de una contraseña.
    """

    return pwd_context.hash(password)


def verify_password(
    plain: str,
    hashed: str,
) -> bool:
    """
    Verifica la contraseña recibida contra el hash almacenado.
    """

    return pwd_context.verify(
        plain,
        hashed,
    )


def create_access_token(
    data: dict,
    minutes: int | None = None,
) -> str:
    """
    Genera un JWT con fecha de expiración.
    """

    to_encode = data.copy()

    if minutes is not None:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=minutes
        )
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=getattr(
                settings,
                "ACCESS_TOKEN_EXPIRE_MINUTES",
                60,
            )
        )

    to_encode.update(
        {
            "exp": expire,
        }
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def register_user(
    db: Session,
    payload: UserCreate,
) -> User:
    """
    Registra un usuario junto a los recursos base del jugador:

    - Usuario
    - Perfil Jugador
    - Nave inicial
    - Salas iniciales
    - Inventario inicial

    Todo se ejecuta dentro de una única transacción.
    """

    existing_user = (
        db.query(User)
        .filter(
            (User.email == payload.email)
            | (User.username == payload.username)
        )
        .first()
    )

    if existing_user:
        raise Exception(
            "El email o el nombre de usuario ya se encuentran registrados."
        )

    password_hash = hash_password(payload.password)

    try:
        new_user = User(
            email=payload.email,
            username=payload.username,
            password_hash=password_hash,
        )

        db.add(new_user)
        db.flush()

        new_player = Jugador(
            user_id=new_user.id,
            nickname=payload.username,
            power=5000,
        )

        db.add(new_player)

        # Mantiene disponible la relación durante esta misma transacción.
        new_user.jugador = new_player

        db.flush()

        # Nave inicial persistente.
        create_initial_ship(
            db=db,
            user_id=new_user.id,
            ship_name=f"Nave de {new_user.username}",
        )

        # Salas iniciales del jugador.
        ship_rooms_service.crear_salas_iniciales(
            db,
            user_id=new_user.id,
        )

        # Inventario inicial del jugador.
        inventory_service.crear_inventario_inicial(
            db,
            player_id=int(new_player.id),
        )

        db.commit()
        db.refresh(new_user)

        return new_user

    except Exception:
        db.rollback()
        raise


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    """
    Valida las credenciales para inicio de sesión.
    """

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
) -> User:
    """
    Extrae el JWT Bearer y retorna al usuario autenticado.
    """

    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[
                settings.ALGORITHM,
            ],
        )

        email: str | None = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None:
        raise credentials_exception

    return user