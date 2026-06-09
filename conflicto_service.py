# app/services/conflicto_service.py
from sqlalchemy.orm import Session
import uuid

# --- Importaciones necesarias ---
from app.models.jugador import Jugador
from app.models.user import User
# TODO: Importar modelos de tripulantes y unidades cuando existan
# from ..models.tripulantes import TripulanteJugador

def _calcular_poder_total(db: Session, jugador: Jugador, unidades: list, ids_tripulantes: list):
    """
    Calcula el poder de combate total de una fuerza, combinando
    el poder base de las unidades con los bonus de tripulantes y equipo.
    """
    # PASO A: PODER DE TROPAS BASE
    poder_tropas_base = 0
    # TODO: Mover esto a una tabla de configuración en la BD
    mapa_poder_base = {"Infanteria": 10, "Drones": 8, "Pilotos": 12, "Escudos": 15, "Canoneros": 20}
    for unidad in unidades:
        poder_tropas_base += mapa_poder_base.get(unidad.get('type'), 0) * unidad.get('quantity', 0)

    # PASO B: BONUS DE TRIPULACIÓN (Fuerza, Inteligencia, etc.)
    bonus_stats_total = 0
    # Lógica Faltante:
    # 1. Cargar tripulantes de la DB usando 'ids_tripulantes'.
    # 2. Sumar sus stats (Fza, Int, Res...).
    # 3. Aplicar multiplicadores: bonus_stats_total += (stats_sumadas.fuerza * 1.5)
    
    # PASO C: BONUS DE EQUIPO
    bonus_equipo_total = 0
    # Lógica Faltante:
    # 1. Cargar el equipo que llevan esos tripulantes de la DB.
    # 2. Sumar todos los bonos porcentuales.
    
    # PASO D: CÁLCULO TOTAL
    poder_total = (poder_tropas_base + bonus_stats_total) * (1 + bonus_equipo_total)
    
    # Placeholder simple mientras se implementa B y C
    if poder_total == 0:
        return 1 # Evitar división por cero
        
    return poder_total

def resolver_conflicto(db: Session, atacante: Jugador, peticion: dict):
    
    # 1. CARGAR DATOS (Atacante)
    datos_atacante = peticion['attacking_force']
    poder_total_atacante = _calcular_poder_total(
        db, 
        atacante, 
        datos_atacante.get('units', []), 
        datos_atacante.get('assigned_crew_ids', [])
    )
    
    # 2. CARGAR DATOS (Defensor)
    # Corrección: Se busca el jugador a través de la relación con el usuario
    defensor = db.query(Jugador).join(User).filter(User.username == peticion['target_username']).first()
    if not defensor:
        raise Exception("Jugador objetivo no encontrado")
    if defensor.id == atacante.id: # type: ignore
        raise Exception("No puedes atacarte a ti mismo")
        
    # Lógica Faltante: Cargar tropas y tripulantes de defensa del defensor
    unidades_defensor = [] # Placeholder
    ids_tripulantes_defensor = [] # Placeholder
    
    poder_total_defensor = _calcular_poder_total(
        db,
        defensor,
        unidades_defensor,
        ids_tripulantes_defensor
    )
    
    # 3. RESOLVER (Paso E - Cálculo de Bajas)
    ratio_poder = poder_total_atacante / poder_total_defensor
    outcome = "win" if ratio_poder > 1 else "loss"
    
    # Lógica Placeholder de Bajas:
    # Lógica Faltante: Calcular 'attacker_losses' y 'defender_losses'
    attacker_losses = []
    defender_losses = []
    
    # Lógica Faltante: Calcular 'resources_gained' (botín)
    resources_gained = []
    
    # 4. APLICAR RESULTADOS (Paso F - Lógica de transacción)
    # La transacción (commit/rollback) se manejará en el endpoint.
    # TODO: Implementar la lógica para aplicar bajas y transferir botín.
        
    # 5. RESPUESTA (Paso G)
    return {
        "status": "resolved",
        "outcome": outcome,
        "conflict_id": str(uuid.uuid4()),
        "attacker_losses": attacker_losses,
        "defender_losses": defender_losses,
        "resources_gained": resources_gained
    }