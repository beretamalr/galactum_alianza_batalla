# app/services/tripulantes_service.py
from sqlalchemy.orm import Session
from app.v2_features_beta.models.costos_tripulantes import TripulanteCostoContratar, TripulanteCostoMejora # type: ignore
# TODO: Necesitarás un modelo para guardar los tripulantes que posee un jugador.
# from ..models.tripulantes import TripulanteJugador 
from app.services.recursos_service import verificar_y_consumir_recursos
import json

def contratar_tripulante(db: Session, jugador_id: int, peticion: dict):
    tripulante_id = peticion['tripulante_id']
    
    # 1. OBTENER EL COSTO DE CONTRATACIÓN
    costo_db = db.query(TripulanteCostoContratar).filter(
        TripulanteCostoContratar.tripulante_id == tripulante_id
    ).first()
    
    if not costo_db:
        raise Exception("Costo de tripulante no definido")
        
    costo_lista = json.loads(costo_db.costo_data)
    
    # 2. VALIDAR Y CONSUMIR RECURSOS (PARTE DE LA TRANSACCIÓN)
    # La excepción de recursos insuficientes se propagará al endpoint.
    verificar_y_consumir_recursos(db, jugador_id, costo_lista)

    # 3. AÑADIR TRIPULANTE AL JUGADOR (LÓGICA PENDIENTE)
    # Cuando tengas el modelo 'TripulanteJugador', descomenta y adapta esta sección:
    # nuevo_tripulante = TripulanteJugador(
    #     jugador_id=jugador_id, 
    #     tripulante_id_base=tripulante_id, 
    #     nivel=1
    # )
    # db.add(nuevo_tripulante)
    
    # Nota: No hay db.commit(). El endpoint se encargará de ello.
    return {"status": "success", "message": f"Tripulante {tripulante_id} contratado"}

def mejorar_tripulante(db: Session, jugador_id: int, peticion: dict):
    # instancia_id = peticion['tripulante_instancia_id']
    nivel_objetivo = peticion['nivel_objetivo']

    # 1. VALIDAR QUE EL TRIPULANTE PERTENECE AL JUGADOR (LÓGICA PENDIENTE)
    # Cuando tengas el modelo 'TripulanteJugador', descomenta y adapta esta sección:
    # tripulante_db = db.query(TripulanteJugador).filter(
    #     TripulanteJugador.id == instancia_id, 
    #     TripulanteJugador.jugador_id == jugador_id
    # ).with_for_update().first() # with_for_update para evitar race conditions
    #
    # if not tripulante_db:
    #   raise Exception("Tripulante no encontrado o no te pertenece")
    # if nivel_objetivo <= tripulante_db.nivel:
    #   raise Exception("El nivel objetivo debe ser superior al actual")

    # 2. OBTENER EL COSTO DE MEJORA
    costo_db = db.query(TripulanteCostoMejora).filter(
        TripulanteCostoMejora.nivel_objetivo == nivel_objetivo
    ).first()
    
    if not costo_db:
        raise Exception("Costo de mejora no definido para ese nivel")

    costo_lista = json.loads(costo_db.costo_data)

    # 3. VALIDAR Y CONSUMIR RECURSOS (PARTE DE LA TRANSACCIÓN)
    verificar_y_consumir_recursos(db, jugador_id, costo_lista)

    # 4. APLICAR MEJORA (LÓGICA PENDIENTE)
    # tripulante_db.nivel = nivel_objetivo
    
    # Nota: No hay db.commit(). El endpoint se encargará de ello.
    return {"status": "success", "message": "Tripulante mejorado al nivel " + str(nivel_objetivo)}