from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session


from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin
from app.services import auth as auth_service
from app.services import ship_rooms_service
from app.services import inventory_service
from app.services import ship

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED, name="Register user")
def register(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        new_user = auth_service.register_user(db, payload)
        access_token = auth_service.create_access_token(data={"sub": new_user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/login", response_model=Token, name="Login user")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verify", name="Verify token")
def verify_token(current_user: User = Depends(auth_service.get_current_user)):
    player = current_user.jugador
    return {
        "message": "Token válido",
        "user_email": current_user.email,
        "player_id": player.id if player else None,
        "player_nickname": player.nickname if player else None,
        "player_power": player.power if player else 0,
        "alliance_id": player.alliance_id if player else None,
    }
