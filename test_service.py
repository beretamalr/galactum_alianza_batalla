import sys
import os
from sqlalchemy.orm import Session

# --- CONFIGURACIÓN DE RUTA ---
# Añade el directorio principal al path para encontrar 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# --- Importaciones de tu proyecto ---
from app.db.dependencies import get_db # Para obtener una sesión de BD
from app.services.ship import start_player_move # ¡La función que queremos probar!
from app.schemas.ship import Position # El 'contrato' de la posición
from app.models.user import User # Para buscar un usuario de prueba

print("--- INICIANDO PRUEBA DEL SERVICIO DE MOVIMIENTO ---")

# Obtenemos una sesión de base de datos.
# 'next(get_db())' es una forma de obtener un solo valor de un generador.
db: Session = next(get_db())

try:
    # --- PASO 1: OBTENER DATOS DE PRUEBA ---
    # Necesitamos un usuario que EXISTA en tu base de datos para la prueba.
    # Buscamos el primer usuario que encontremos.
    print("Buscando un usuario de prueba en la BD...")
    test_user = db.query(User).first()
    
    if not test_user:
        raise Exception("No se encontró ningún usuario en la base de datos. Por favor, crea uno para poder probar.")
        
    user_id_de_prueba = test_user.id
    print(f"Usuario de prueba encontrado: {test_user.username} (ID: {user_id_de_prueba})")
    
    # Define un destino para la prueba
    posicion_objetivo = Position(x=500.0, y=750.0)
    print(f"Moviendo la nave a la posición: x={posicion_objetivo.x}, y={posicion_objetivo.y}")

    # --- PASO 2: LLAMAR A LA FUNCIÓN DEL SERVICIO ---
    # ¡Aquí está la magia! Llamamos a tu función directamente.
    print("\nLlamando a la función 'start_player_move'...")
    resultado = start_player_move(
        db=db, 
        user_id=str(user_id_de_prueba), 
        target_pos=posicion_objetivo
    )
    
    # --- PASO 3: VERIFICAR EL RESULTADO ---
    print("\n¡LA FUNCIÓN SE EJECUTÓ CON ÉXITO!")
    print("Resultado devuelto por la función:")
    print(f"  - Posición Final: {resultado.endPosition}")
    print(f"  - Hora de llegada estimada: {resultado.estimatedArrivalTime}")

    # Ahora, verifica en tu base de datos (NeonDB) si la nave de este usuario
    # tiene 'is_moving' en 'true' y las nuevas coordenadas.

except Exception as e:
    print(f"\n¡ERROR DURANTE LA PRUEBA! La función falló. {e}")
    print(f"Detalle del error: {e}")

finally:
    # Cerramos la conexión a la base de datos
    db.close()
    print("\n--- PRUEBA FINALIZADA ---")
'''

### ¿Cómo usar este script?

1.  **Asegúrate de tener datos:** Este script asume que tienes al menos **un usuario** y **una nave** asociada a ese usuario en tu base de datos. Si no, fallará.
2.  **Ejecútalo desde la terminal:**
    
bash
python test_service.py
    
'''