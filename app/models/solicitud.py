
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class SolicitudCrear(BaseModel):
    asunto: str = Field(min_length=3, max_length=500)
    remitente: Optional[str] = None
    dependencia_id: Optional[UUID] = None
    correo_message_id: Optional[str] = None
    codigo_publicacion: Optional[str] = None


class SolicitudEstadoActualizar(BaseModel):
    estado: str
    observaciones: Optional[str] = None


class SolicitudRespuesta(BaseModel):
    id: UUID
    dependencia_id: Optional[UUID]
    correo_message_id: Optional[str]
    asunto: str
    remitente: Optional[str]
    codigo_publicacion: Optional[str]
    fecha_recepcion: datetime
    estado: str
    observaciones: Optional[str]
