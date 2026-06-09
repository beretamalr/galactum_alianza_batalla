# app/services/misiones_service.py
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from app.models.misiones import MisionJugador
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
    # --- CORRECCIÓN: Importación Local ---
    # Importamos el servicio aquí para romper el ciclo de importación.
    from app.services.recursos_service import agregar_recursos_jugador

    mision_id = peticion['mision_id']
    mision_jugador = db.query(MisionJugador).options(
        joinedload(MisionJugador.mision_maestra)
    ).filter(
        MisionJugador.jugador_id == jugador_id,
        MisionJugador.mision_id == mision_id
    ).with_for_update().first()
    
    if not mision_jugador:
        raise Exception("Misión no encontrada")
    if mision_jugador.estado == 'reclamada':  # type: ignore
        raise Exception("Recompensa ya reclamada")
    if mision_jugador.estado != 'completada':  # type: ignore
        raise Exception("Misión no completada")
        
    mision_jugador.estado = 'reclamada'  # type: ignore
    recompensa_lista = json.loads(mision_jugador.mision_maestra.recompensa_data)
    agregar_recursos_jugador(db, jugador_id, recompensa_lista)
    
    return {"status": "success", "message": "Recompensa reclamada.", "recursos_ganados": recompensa_lista}

def actualizar_progreso_mision(db: Session, jugador_id: int, tipo_objetivo: str, objetivo_id: str | None = None, cantidad: int = 1):
    """
    Hook para actualizar el progreso de misiones activas basado en una acción del jugador.
    No hace commit, debe ser parte de una transacción mayor.
    """
    # Busca misiones activas del jugador que coincidan con el tipo de objetivo.
    # El objetivo_id_requerido puede ser NULL (para misiones genéricas como "mina cualquier recurso").
    misiones_a_actualizar = db.query(MisionJugador).join(MisionJugador.mision_maestra).filter(
        MisionJugador.jugador_id == jugador_id,
        MisionJugador.estado == 'activa',
        MisionJugador.mision_maestra.tipo_objetivo == tipo_objetivo,
        (MisionJugador.mision_maestra.objetivo_id_requerido.is_(None)) | (MisionJugador.mision_maestra.objetivo_id_requerido == objetivo_id) # type: ignore
    ).all()

    for mision in misiones_a_actualizar:
        if mision.estado == 'activa': # type: ignore
            mision.progreso_actual += cantidad # type: ignore
            # Si el progreso alcanza o supera el requisito, se marca como completada.
            if mision.progreso_actual >= mision.mision_maestra.cantidad_requerida: # type: ignore
                mision.estado = 'completada' # type: ignore
                mision.progreso_actual = mision.mision_maestra.cantidad_requerida # Clamp progress to max

    # El commit se maneja en el servicio que llama a este hook (ej. upgrade_room).