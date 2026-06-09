# app/services/auth.py
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
# ⬇️ Cambiamos a HTTP Bearer (quitamos OAuth2PasswordBearer)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.user import UserCreate
from app.services import ship, ship_rooms_service, inventory_service # <-- ¡Importamos los servicios!

from app.models.user import User
from app.models.jugador import Jugador


settings = get_settings()

# Hash de contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ⬇️ Esquema de autenticación tipo "Bearer <token>"
bearer_scheme = HTTPBearer()  # auto_error=True por defecto: si falta el header, devuelve 401


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, minutes: int | None = None) -> str:
    """
    Genera un JWT con expiración.
    Espera que en `data` venga, por ejemplo, {"sub": "<username|email>"}.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Busca un usuario por su email.
    """
    return db.execute(select(User).where(User.email == email)).scalars().first()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """
    Busca un usuario por email y verifica su contraseña.
    Devuelve el objeto User si es exitoso, si no, None.
    """
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):  # type: ignore
        return None
    return user


def register_user(db: Session, payload: UserCreate) -> User:
    """
    Handles the business logic of creating a new user, their associated ship,
    player, and the initial ship rooms.
    """
    # 1. Preparación de datos
    password_hash = hash_password(payload.password)
    
    # --- INICIO DE LA TRANSACCIÓN ---
    try:
        # 2. CREAR USUARIO (USER)
        new_user = User(
            email=payload.email,
            username=payload.username,
            password_hash=password_hash
        )
        db.add(new_user)
        db.flush() # Necesario para obtener new_user.id
    
        # 3. CREAR JUGADOR (PLAYER)
        # El jugador está ligado al ID del usuario (user_id = user.id)
        new_player = Jugador(
            user_id=new_user.id,
            nickname=payload.username
        )
        db.add(new_player)
        db.flush() # ¡CORRECCIÓN! Es necesario para que la relación user.jugador se actualice en la sesión.
    
        # --- ORQUESTACIÓN DE SERVICIOS ---

        # 4. CREAR NAVE (SHIP) llamando al servicio correspondiente
        # El servicio se encarga de la lógica de la posición aleatoria.
        ship.create_initial_ship(db, user_id=str(new_user.id))

        # 5. CREAR SALAS INICIALES (SHIP ROOMS) llamando al servicio
        # Corrección: Pasamos el user_id, como espera la función corregida.
        ship_rooms_service.crear_salas_iniciales(db, user_id=new_user.id) # type: ignore

        # 6. CREAR INVENTARIO INICIAL (STARTER PACK)
        inventory_service.crear_inventario_inicial(db, player_id=new_player.id)

        # --- FIN DE LA ORQUESTACIÓN ---
    
        # 6. CONFIRMAR TRANSACCIÓN
        db.commit()
        db.refresh(new_user)
        
        return new_user

    except Exception as e:
        # 7. REVERTIR TRANSACCIÓN en caso de error
        db.rollback()
        raise e


def get_current_user(
    db: Session = Depends(get_db),
    # ⬇️ En vez de token: str = Depends(oauth2_scheme)
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    """
    Extrae el token del header Authorization: Bearer <token>,
    lo valida y retorna el usuario autenticado.
    """
    token = credentials.credentials  # el valor del JWT sin la palabra 'Bearer'

    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        sub: str | None = payload.get("sub")
        if sub is None:
            raise cred_exc
    except JWTError:
        # token inválido / expirado / mal firmado
        raise cred_exc

    user = get_user_by_email(db, sub) # Usamos la función corregida
    if not user:
        raise cred_exc
    return user
