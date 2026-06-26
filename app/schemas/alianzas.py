from pydantic import BaseModel, ConfigDict, Field

class AlianzaCrearPeticion(BaseModel):
    nombre: str
    tag: str

class AlianzaRespuesta(BaseModel):
    id: int
    # Usamos Field con validation_alias para mapear 'name' de la BD a 'nombre' en el JSON
    nombre: str = Field(validation_alias="name")
    tag: str
    
    # Ponemos valores por defecto por si la base de datos no tiene la columna exacta
    nivel: int = Field(default=1, validation_alias="level")
    members_count: int = Field(default=1)
    max_members: int = Field(default=100)
    power: str = Field(default="0")
    lang: str = Field(default="ES")
    puntos_prestigio: int = Field(default=0)

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )