# app/v2_features_beta/services/alianzas_service.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from ...v2_features_beta.models.alianzas import Alianza, MiembroAlianza, Asedio, RefuerzoAsedio # type: ignore
from ...services.recursos_service import verificar_y_consumir_recursos
from datetime import datetime, timedelta
import json

# Define aquí el costo de fundar una alianza
COSTO_FUNDAR_ALIANZA = [{"id": "Roderitium", "qty": 100000}] # Ejemplo

def crear_alianza(db: Session, jugador_id: int, peticion: dict):
    # 1. Validar nombre y tag en una sola consulta para eficiencia
    nombre = peticion['nombre']
    tag = peticion['tag']
    alianza_existente = db.query(Alianza).filter(or_(Alianza.nombre == nombre, Alianza.tag == tag)).first()
    if alianza_existente:
        if alianza_existente.nombre == nombre:
            raise Exception("El nombre de la alianza ya existe")
        else:
            raise Exception("El tag de la alianza ya existe")

    # 2. Validar que el jugador no esté en otra alianza
    miembro_existente = db.query(MiembroAlianza).filter(MiembroAlianza.jugador_id == jugador_id).first()
    if miembro_existente:
        raise Exception("El jugador ya pertenece a una alianza")

    # 3. Consumir recursos (parte de la transacción)
    # La excepción de recursos insuficientes se propagará hacia arriba.
    verificar_y_consumir_recursos(db, jugador_id, COSTO_FUNDAR_ALIANZA)

    # 4. Crear Alianza y Miembro (Líder)
    nueva_alianza = Alianza(
        nombre=nombre,
        tag=tag,
        descripcion=peticion.get('descripcion'),
        owner_jugador_id=jugador_id
    )
    db.add(nueva_alianza)
    db.flush() # Para obtener el alianza_id antes del commit

    nuevo_miembro = MiembroAlianza(
        alianza_id=nueva_alianza.alianza_id,
        jugador_id=jugador_id,
        rol='lider'
    )
    db.add(nuevo_miembro)
    
    # Nota: No hay db.commit(). El endpoint se encargará de ello.
    return nueva_alianza # Devolvemos el objeto creado

def iniciar_asedio(db: Session, jugador_id: int, planeta_id: str):
    # 1. Validar que el jugador es 'lider' u 'oficial'
    miembro = db.query(MiembroAlianza).filter(MiembroAlianza.jugador_id == jugador_id).first()
    if not miembro or miembro.rol not in ['lider', 'oficial']:
        raise Exception("No autorizado para iniciar asedio")

    # 2. Validar que el planeta no esté ya en asedio activo
    asedio_existente = db.query(Asedio).filter(Asedio.planeta_id == planeta_id, Asedio.fecha_fin > datetime.utcnow()).first()
    if asedio_existente:
        raise Exception("El planeta ya está bajo asedio")

    # 3. Crear Asedio (Duración de 24h)
    fecha_fin = datetime.utcnow() + timedelta(hours=24)
    nuevo_asedio = Asedio(
        planeta_id=planeta_id,
        alianza_atacante_id=miembro.alianza_id,
        fecha_fin=fecha_fin
    )
    db.add(nuevo_asedio)
    db.flush() # Para obtener el ID del asedio
    
    return nuevo_asedio

def enviar_refuerzo(db: Session, jugador_id: int, asedio_id: int, peticion: dict):
    # 1. Validar asedio y pertenencia a la alianza en una sola consulta
    asedio = db.query(Asedio).options(
        joinedload(Asedio.alianza).joinedload(Alianza.miembros)
    ).filter(
        Asedio.asedio_id == asedio_id, 
        Asedio.fecha_fin > datetime.utcnow()
    ).first()

    if not asedio:
        raise Exception("Asedio no encontrado o finalizado")

    miembro = db.query(MiembroAlianza).filter(MiembroAlianza.jugador_id == jugador_id, MiembroAlianza.alianza_id == asedio.alianza_atacante_id).first()
    if not miembro:
        raise Exception("No perteneces a la alianza atacante")

    # 2. Consumir recursos y unidades
    # (Necesitarás una función 'verificar_y_consumir_unidades' similar a la de recursos)
    # verificar_y_consumir_recursos(db, jugador_id, peticion.get('recursos_enviados', []))
    # verificar_y_consumir_unidades(db, jugador_id, peticion.get('unidades_enviadas', []))

    # 3. Crear registro de refuerzo
    nuevo_refuerzo = RefuerzoAsedio(
        asedio_id=asedio_id,
        jugador_id=jugador_id,
        unidades_enviadas=json.dumps(peticion.get('unidades_enviadas', [])),
        recursos_enviados=json.dumps(peticion.get('recursos_enviados', []))
    )
    db.add(nuevo_refuerzo)
    
    return nuevo_refuerzo