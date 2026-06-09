import sys
import os
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.dependencies import get_db
from app.db.base import Base
from app.main import app


# =========================================================
# 1️⃣ Añadir la raíz del proyecto al PYTHONPATH
# =========================================================
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# =========================================================
# 2️⃣ Cargar variables de entorno desde .env
# =========================================================
env_path = os.path.join(ROOT_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    print("⚠️  No se encontró archivo .env en la raíz del proyecto")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("No se encontró DATABASE_URL en .env")

print(f"Usando DATABASE_URL: {DATABASE_URL}")

# =========================================================
# 3️⃣ Configurar SQLite en memoria para tests de auth
# =========================================================
SQLALCHEMY_TEST_URL = "sqlite:///:memory:"
engine_test = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# Crear tablas temporales
Base.metadata.create_all(bind=engine_test)

# Sobrescribir get_db para usar SQLite temporal en test_auth.py
def override_get_db():
    db = None
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        if db:
            db.close()

app.dependency_overrides[get_db] = override_get_db

# =========================================================
# 4️⃣ Detectar argumentos para seleccionar tests
# =========================================================
# Por defecto: todos los tests
default_test_files = []

# Revisar si existe carpeta 'tests'
tests_folder = os.path.join(ROOT_DIR, "tests")
if os.path.exists(tests_folder):
    default_test_files.append(tests_folder)
else:
    # Archivos de test en la raíz
    for f in ["test_auth.py", "test_jugadores.py"]:
        file_path = os.path.join(ROOT_DIR, f)
        if os.path.exists(file_path):
            default_test_files.append(file_path)

# Revisar argumentos
if len(sys.argv) > 1:
    arg = sys.argv[1].lower()
    if arg == "--auth":
        default_test_files = [os.path.join(ROOT_DIR, "test_auth.py")]
    elif arg == "--jugadores":
        default_test_files = [os.path.join(ROOT_DIR, "test_jugadores.py")]
    else:
        print(f"⚠️ Argumento desconocido '{arg}', se ejecutarán todos los tests")

# =========================================================
# 5️⃣ Ejecutar pytest
# =========================================================
print(f"\n=== Ejecutando pruebas: {default_test_files} ===\n")
exit_code = pytest.main(["-v"] + default_test_files)

# =========================================================
# 6️⃣ Cerrar engine SQLite en memoria (por seguridad)
# =========================================================
engine_test.dispose()

sys.exit(exit_code)
