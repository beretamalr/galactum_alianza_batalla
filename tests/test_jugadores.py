# test_jugadores.py

from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy import text

# Cargar variables de entorno
load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL) # type: ignore

# Construir la URL de conexión
#DB_USER = os.getenv("DB_USER")
#DB_PASSWORD = os.getenv("DB_PASSWORD")
#DB_HOST = os.getenv("DB_HOST")
#DB_PORT = os.getenv("DB_PORT")
#DB_NAME = os.getenv("DB_NAME")

#DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear engine de SQLAlchemy
engine = create_engine(DATABASE_URL) # type: ignore

# Consultar y mostrar los registros de la tabla 'jugador'
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM jugador"))
    jugadores = result.fetchall()
    for jugador in jugadores:
        print(jugador)