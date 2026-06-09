# app/v2_features_beta/services/misiones_service.py
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from ...v2_features_beta.models.misiones import MisionJugador # type: ignore
from ...services.recursos_service import agregar_recursos_jugador
import json

def obtener_misiones(db: Session, jugador_id: int):
    # Usamos joinedload para cargar la relación y evitar N+1 queries
    misiones_db = db.query(MisionJugador).options(
        joinedload(MisionJugador.mision_maestra)
    ).filter(MisionJugador.jugador_id == jugador_id).all()
    
    misiones_diarias_resp = []
    misiones_historia_resp = []
    
    for mision_jugador in misiones_db:
        maestra = mision_jugador.mision_maestra 
        if not maestra:
            continue # Ignorar misiones huérfanas
            
        recompensa_lista = json.loads(maestra.recompensa_data)
        
        mision_schema = {
            "mision_id": maestra.mision_id,
            "titulo": maestra.titulo,
            "descripcion": maestra.descripcion,
            "progreso_actual": mision_jugador.progreso_actual,
            "cantidad_requerida": maestra.cantidad_requerida,
            "estado": mision_jugador.estado,
            "recompensa": recompensa_lista
        }
        
        if maestra.tipo_mision == 'diaria':
            misiones_diarias_resp.append(mision_schema)
        else:
            misiones_historia_resp.append(mision_schema)
            
    return {"status": "success", "misiones_diarias": misiones_diarias_resp, "misiones_historia": misiones_historia_resp}

def reclamar_recompensa(db: Session, jugador_id: int, peticion: dict):
    mision_id = peticion['mision_id']
    # Usamos with_for_update para bloquear la fila y evitar race conditions
    mision_jugador = db.query(MisionJugador).options(
        joinedload(MisionJugador.mision_maestra)
    ).filter(
        MisionJugador.jugador_id == jugador_id,
        MisionJugador.mision_id == mision_id
    ).with_for_update().first()
    
    if not mision_jugador:
        raise Exception("Misión no encontrada")
        
    if mision_jugador.estado == 'reclamada':
        raise Exception("Recompensa ya reclamada")
        
    if mision_jugador.estado != 'completada':
        raise Exception("Misión no completada")
        
    # 1. Cambiar estado de la misión
    mision_jugador.estado = 'reclamada'
    
    # 2. Añadir recursos usando el servicio de recursos
    recompensa_lista = json.loads(mision_jugador.mision_maestra.recompensa_data)
    agregar_recursos_jugador(db, jugador_id, recompensa_lista)
    
    # Nota: No hacemos db.commit() aquí. El endpoint se encargará de ello.
    
    return {"status": "success", "message": "Recompensa reclamada.", "recursos_ganados": recompensa_lista}