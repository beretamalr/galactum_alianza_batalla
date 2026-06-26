# app/api/routes/inventario.py
from fastapi import APIRouter, Depends, status
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/inventario", tags=["Inventario"])

@router.get("/materiales", status_code=status.HTTP_200_OK, name="Ver Inventario de Recursos")
def ver_inventario(current_user: User = Depends(get_current_user)):
    """
    Retorna la bodega de carga del jugador con la cantidad exacta de materiales almacenados.
    """
    return {
        "comandante": current_user.username,
        "bodega": [
            {"recurso": "Helio-3", "cantidad": 250, "unidad": "litros"},
            {"recurso": "Titanio", "cantidad": 45, "unidad": "placas"},
            {"recurso": "Créditos Galácticos", "cantidad": 12000, "unidad": "sc"}
        ]
    }