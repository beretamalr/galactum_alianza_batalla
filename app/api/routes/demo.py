from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.services.demo_data import DEMO_CREDENTIALS, seed_demo_data

router = APIRouter(prefix="/demo", tags=["Demo"])


@router.post("/bootstrap", name="Bootstrap demo data")
def bootstrap_demo_data(db: Session = Depends(get_db)):
    """
    Crea o completa los datos falsos mínimos para probar el backend con Godot.
    La operación es idempotente: se puede ejecutar varias veces sin duplicar filas.
    """
    return seed_demo_data(db)


@router.get("/credentials", name="Get demo credentials")
def get_demo_credentials():
    return DEMO_CREDENTIALS