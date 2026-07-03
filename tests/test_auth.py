# tests/test_auth.py
import os
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.dependencies import get_db
from app.db.base import Base
from app.models.asteroid import Asteroid
from app.models.inventory import Inventory
from app.models.jugador import Jugador
from app.models.server import Server
from app.models.ship_rooms import ShipRoom
from app.models.ship import Ship
from app.models.tripulante import Tripulante
from app.models.user import User
import pytest

# =========================================================
# 🔹 CONFIGURAR BASE DE DATOS ANTES DE IMPORTAR app
# =========================================================
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_QlH8JPun0ZFh@ep-restless-hall-adcqdaif-pooler.c-2.us-east-1.aws.neon.tech/neondb"

from app.main import app  # <-- Importar después de setear DATABASE_URL

# =========================================================
# 🔹 CONFIGURACIÓN DE SESIÓN DE TEST
# =========================================================
SQLALCHEMY_TEST_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")
engine_test = create_engine(SQLALCHEMY_TEST_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# Crear tablas si no existen
Base.metadata.create_all(bind=engine_test)

# Sobrescribir la dependencia get_db de FastAPI
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# =========================================================
# 🔹 LIMPIEZA ENTRE TESTS
# =========================================================
@pytest.fixture(autouse=True)
def clear_users_table():
    db = TestingSessionLocal()
    db.query(Tripulante).delete()
    db.query(ShipRoom).delete()
    db.query(Inventory).delete()
    db.query(Asteroid).delete()
    db.query(Ship).delete()
    db.query(Server).delete()
    db.query(Jugador).delete()
    db.query(User).delete()
    db.commit()
    db.close()


# =========================================================
# 🔹 TESTS DE AUTENTICACIÓN
# =========================================================
def test_register_user():
    unique = str(uuid.uuid4())[:8]
    response = client.post("/api/v1/auth/register", json={
        "username": f"test_user_{unique}",
        "email": f"test_{unique}@mail.com",
        "password": "1234"
    })
    assert response.status_code == 201
    data = response.json()
    assert "token" in data


def test_login_user():
    unique = str(uuid.uuid4())[:8]
    client.post("/api/v1/auth/register", json={
        "username": f"login_user_{unique}",
        "email": f"login_{unique}@mail.com",
        "password": "1234"
    })

    # Login con username
    response = client.post("/api/v1/auth/login", json={
        "username_or_email": f"login_user_{unique}",
        "password": "1234"
    })
    assert response.status_code == 200
    assert "token" in response.json()

    # Login con email
    response = client.post("/api/v1/auth/login", json={
        "username_or_email": f"login_{unique}@mail.com",
        "password": "1234"
    })
    assert response.status_code == 200
    assert "token" in response.json()


def test_invalid_login():
    response = client.post("/api/v1/auth/login", json={
        "username_or_email": "noexist@mail.com",
        "password": "incorrecta"
    })
    assert response.status_code in (401, 404)


def test_verify_token():
    unique = str(uuid.uuid4())[:8]
    reg = client.post("/api/v1/auth/register", json={
        "username": f"verify_user_{unique}",
        "email": f"verify_{unique}@mail.com",
        "password": "1234"
    })
    assert reg.status_code == 201
    token = reg.json()["token"]

    # Verificar token
    response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == f"verify_user_{unique}"
    assert data["email"] == f"verify_{unique}@mail.com"
