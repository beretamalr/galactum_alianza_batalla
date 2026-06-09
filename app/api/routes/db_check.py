from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.dependencies import get_db

router = APIRouter(prefix="/api/v1", tags=["database"])

@router.get("/db-check", name="Database check")
def db_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT NOW()")).scalar()
    return {"database_time": result}
