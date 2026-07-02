import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text

from app.db.session import engine


def main():
    inspector = inspect(engine)
    columns = [column["name"] for column in inspector.get_columns("jugadores")]

    if "alliance_id" in columns:
        print("La columna jugadores.alliance_id ya existe.")
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE jugadores ADD COLUMN alliance_id INTEGER"))
        connection.execute(text("ALTER TABLE jugadores ADD CONSTRAINT jugadores_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES alliances(id)"))

    print("Columna jugadores.alliance_id creada correctamente.")


if __name__ == "__main__":
    main()