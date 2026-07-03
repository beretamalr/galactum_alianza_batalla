# app/schemas/token.py
from pydantic import BaseModel
from typing import Optional

# Este es el nuevo esquema para las respuestas de registro y login
class TokenResponse(BaseModel):
    status: str = "success"
    message: str
    access_token: str
    token_type: str = "bearer"
    token: str

class TokenData(BaseModel):
    username: Optional[str] = None