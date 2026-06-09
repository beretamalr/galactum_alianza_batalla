from sqlalchemy import Column, String, Text, Integer, ForeignKey, UniqueConstraint, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class CatalogoItem(Base):
    __tablename__ = "catalogo_items"
    # ELIMINADO: __table_args__ = {'schema': 'public'} -> Ya no es necesario
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text)
    tipo = Column(String, nullable=False) # ej: 'recurso', 'componente', 'equipamiento'
    rareza = Column(String(50), nullable=True)
    produccion_min = Column(Integer, nullable=True)
    produccion_max = Column(Integer, nullable=True)
    energia_necesaria = Column(Integer, nullable=True)
    imagen_url = Column(String(255), nullable=True)
    
    # Configuración para 'DEFAULT CURRENT_TIMESTAMP'
    creado_en = Column(TIMESTAMP, server_default=func.now(), nullable=True)

class RecetaCrafteo(Base):
    __tablename__ = "recetas_crafteo"
    
    # Mantenemos solo la restricción única, quitamos el esquema
    __table_args__ = (
        UniqueConstraint('item_resultado_id', 'item_requerido_id', name='uniq_resultado_requerido'),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # SIMPLIFICADO: Quitamos 'public.' del inicio
    item_resultado_id = Column(Integer, ForeignKey('catalogo_items.id'), nullable=False)
    item_requerido_id = Column(Integer, ForeignKey('catalogo_items.id'), nullable=False)
    
    cantidad = Column(Integer, nullable=False)

    # CORREGIDO: Usamos el nombre de la clase "CatalogoItem", no el de la tabla
    item_resultado = relationship(
        "CatalogoItem", 
        foreign_keys=[item_resultado_id],
        backref="recetas_produccion"
    )

    item_requerido = relationship(
        "CatalogoItem", 
        foreign_keys=[item_requerido_id], 
        backref="recetas_uso"
    )