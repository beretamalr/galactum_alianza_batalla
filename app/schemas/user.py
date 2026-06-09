# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: UUID        # <--- 2. CAMBIO CLAVE: De 'int' a 'UUID'
    username: str   # <--- 3. RECOMENDACIÓN: Agregué esto para que el front sepa el nombre
    email: EmailStr
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None