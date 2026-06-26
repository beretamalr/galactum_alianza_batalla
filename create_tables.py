import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "."
        )
    )
)

from dotenv import load_dotenv
from sqlalchemy import create_engine

from app.db.base import Base
from app.core.config import get_settings

# IMPORTAR TODOS LOS MODELOS
from app.models.user import User  # noqa: F401
from app.models.jugador import Jugador  # noqa: F401
from app.models.ship_rooms import ShipRoom  # noqa: F401
from app.models.inventory import Inventory  # noqa: F401

# IMPORTA AQUÍ CUALQUIER OTRO MODELO
# from app.models.mision import Mision
# from app.models.tripulante import Tripulante

load_dotenv()

settings = get_settings()

def main():
    try:

        if not settings.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL no está configurada"
            )

        print("Conectando a Neon PostgreSQL...")

        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
        )

        with engine.connect():
            print("Conexión exitosa.")

        print("Creando tablas...")

        Base.metadata.create_all(bind=engine)

        print("Tablas creadas correctamente.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()