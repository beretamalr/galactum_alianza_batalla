# Script que rellena la base de datos tabla "asteroids" con 200 asteroides aelatorios.

import sys
import os

# --- FIX: AGREGAR RUTA DEL PROYECTO ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import uuid
from app.db.session import SessionLocal 
from app.models.asteroid import Asteroid
from app.models.user import User
from app.models.jugador import Jugador
from app.models.server import Server
from app.models.ship import Ship
from app.models.inventory import Inventory
from app.models.ship_rooms import ShipRoom
from app.models.tripulante import Tripulante
from app.models.crafting import CatalogoItem

def seed_universe():
    db = SessionLocal()
    
    # Limpiamos la tabla primero
    try:
        db.query(Asteroid).delete()
        db.commit()
    except Exception as e:
        print(f"Advertencia al limpiar tabla: {e}")
        db.rollback()
    
    print("Generando universo...")
    
    for _ in range(200): # Generar 200 asteroides
        x = random.uniform(-10000, 10000)
        y = random.uniform(-10000, 10000)


        item = random.randint(1, 7)
        amount = random.randint(1, 7)

        '''
        roll = random.random()
        if roll < 0.6:
            rtype = "Hierro"
            amount = random.randint(100, 500)
        elif roll < 0.9:
            rtype = "Cristal"
            amount = random.randint(50, 200)
        else:
            rtype = "Oro"
            amount = random.randint(10, 100)
        '''    
        # Generamos UUIDs
        pk_id = str(uuid.uuid4())        # Para la Primary Key 'id'
        logic_id = f"ast_{uuid.uuid4()}" # Para la columna única 'asteroid'
            
        asteroid = Asteroid(
            # Nombres exactos según app/models/asteroid.py
            id=pk_id,                   # Primary Key (String)
            asteroid=logic_id,          # Columna 'asteroid' (String único)
            position_x=x,               
            position_y=y,               
            resource_id=item,
            cantidad_maxima=amount,     # Campo en español
            cantidad_restante=amount,   # Campo en español
            is_active=True, 
            reaparecer_en=None          # Campo en español
        )
        db.add(asteroid)
    
    db.commit()
    print("¡Universo creado con 200 asteroides!")

if __name__ == "__main__":
    seed_universe()