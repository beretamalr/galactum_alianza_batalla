# app/api/routes/recursos.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/recursos", tags=["Economía e Intercambio"])

@router.get("/mercado", status_code=status.HTTP_200_OK, name="Ver Mercado Galáctico")
def ver_mercado(current_user: User = Depends(get_current_user)):
    """
    Muestra el listado de precios de los bienes en la estación comercial.
    """
    return [
        {"recurso": "Helio-3", "precio_compra": 15, "precio_venta": 10},
        {"recurso": "Titanio", "precio_compra": 50, "precio_venta": 35}
    ]

@router.post("/comerciar", status_code=status.HTTP_200_OK, name="Comerciar Recursos")
def comerciar_recursos(recurso: str, cantidad: int, tipo_operacion: str, current_user: User = Depends(get_current_user)):
    """
    Procesa la compra o venta de recursos a cambio de Créditos Galácticos.
    """
    if tipo_operacion.lower() not in ["compra", "venta"]:
        raise HTTPException(status_code=400, detail="Operación inválida. Debe ser 'compra' o 'venta'.")
        
    total_creditos = cantidad * (15 if tipo_operacion.lower() == "compra" else 10)
    
    return {
        "status": "transaction_completed",
        "mensaje": f"Operación de {tipo_operacion} procesada para {current_user.username}.",
        "detalles": {
            "recurso": recurso,
            "cantidad": cantidad,
            "creditos_transferidos": total_creditos
        }
    }