# Importaciones de sistema para arreglar el path de importación
import sys
import os

# Añade el directorio principal del proyecto al path de Python
# para que pueda encontrar la carpeta 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))


# --- El resto del código es similar, pero con la importación corregida ---
from dotenv import load_dotenv
from sqlalchemy import create_engine

# ¡IMPORTACIÓN CORREGIDA!
# Basado en tu proyecto, la clase Base probablemente está en db/base.py
from app.db.base import Base 
from app.core.config import get_settings

# --- ¡¡AQUÍ ESTÁ LA SOLUCIÓN!! ---
# SQLAlchemy necesita "ver" la definición de tus modelos para poder crearlos.
from app.models.user import User  # noqa: F401
from app.models.jugador import Jugador  # noqa: F401
from app.models.ship_rooms import ShipRoom  # noqa: F401
from app.models.inventory import Inventory  # noqa: F401

# ... (importa cualquier otro modelo que tengas)


# Carga las variables de entorno desde tu archivo .env
print("Cargando configuración desde el archivo .env...")
load_dotenv()

settings = get_settings()

# Construye la URL de conexión a la base de datos de Supabase
if not all([settings.DB_USER, settings.DB_PASSWORD, settings.DB_HOST, settings.DB_PORT, settings.DB_NAME, settings.DATABASE_URL]):
    raise ValueError("Una o más variables de entorno de la base de datos no están definidas en tu archivo .env")

#DATABASE_URL = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"


def main():
    try:
        # Crea el "motor" de SQLAlchemy con la URL de Supabase
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL no está configurada en las variables de entorno")
        engine = create_engine(settings.DATABASE_URL) # type: ignore
        
        print("Conectando a la base de datos en Supabase...")
        engine.connect()
        print("Conexión exitosa.")

        print("Creando todas las tablas si no existen...")
        # SQLAlchemy crea las tablas en Supabase
        Base.metadata.create_all(bind=engine)
        print("¡Listo! Las tablas han sido creadas exitosamente en Supabase.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")


if __name__ == "__main__":
    main()

# Requerimientos adicionales
# fastapi
# sqlalchemy
# psycopg2-binary
# pydantic
# pydantic-settings
# uvicorn
# bcrypt
# python-jose
# passlib