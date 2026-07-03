from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AlianzaCrearPeticion(BaseModel):
    nombre: str = Field(min_length=3, max_length=50)
    tag: str = Field(min_length=2, max_length=10)
    req_poder: int = Field(default=0, ge=0)


class AlianzaRespuesta(BaseModel):
    id: int
    nombre: str = Field(validation_alias="name")
    tag: str
    nivel: int = Field(validation_alias="level")
    miembros_actuales: int = Field(validation_alias="members_count")
    miembros_maximos: int = Field(validation_alias="max_members")
    poder_total: str = Field(validation_alias="power")
    region: str = Field(validation_alias="lang")
    req_poder: int = Field(validation_alias="required_power")
    puntos_prestigio: int
    lider_jugador_id: int | None = Field(default=None, validation_alias="leader_jugador_id")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MiembroAlianzaRespuesta(BaseModel):
    jugador_id: int
    nombre: str
    poder: int
    es_lider: bool


class AlianzaDetalleRespuesta(AlianzaRespuesta):
    miembros: list[MiembroAlianzaRespuesta]


class SolicitudCrearPeticion(BaseModel):
    mensaje: str = Field(default="", max_length=300)


class SolicitudAlianzaRespuesta(BaseModel):
    id: int
    alianza_id: int
    estado: str
    mensaje: str | None
    creada_en: datetime | None
    solicitante: MiembroAlianzaRespuesta


class OperacionRespuesta(BaseModel):
    mensaje: str
