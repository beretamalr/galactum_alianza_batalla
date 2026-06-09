# app/api/routes/health.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["default"])

@router.get("/health", name="Health")
def health():
    return {"status": "ok"}

@router.get("/", name="Root")
def root():
    return {"message": "Galactum SGM API funcionando correctamente"}


#para testear desde el frontend antes de implementar autenticación.
@router.get("/public-info", name="Public info")
def public_info():
    return {"msg": "Este endpoint no requiere autenticación", "version": "0.1.0"}
