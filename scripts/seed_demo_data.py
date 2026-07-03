import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.services.demo_data import seed_demo_data


def main():
    db = SessionLocal()
    try:
        result = seed_demo_data(db)
        print("Seed demo completado correctamente.")
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()