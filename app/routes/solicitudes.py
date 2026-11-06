
from fastapi import APIRouter, HTTPException
from uuid import UUID

from app.models.solicitud import (
    SolicitudCrear,
    SolicitudEstadoActualizar
)

from app.services.solicitud_service import solicitud_service


router = APIRouter(
    prefix="/solicitudes",
    tags=["Solicitudes"]
)


@router.post("/")
def crear_solicitud(datos: SolicitudCrear):
    try:
        return solicitud_service.crear_solicitud(
            datos.model_dump(mode="json")
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al registrar la solicitud."
        )


@router.get("/")
def listar_solicitudes():
    try:
        return solicitud_service.listar_solicitudes()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar las solicitudes."
        )


@router.get("/{solicitud_id}")
def obtener_solicitud(solicitud_id: UUID):
    try:
        return solicitud_service.obtener_solicitud(solicitud_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.patch("/{solicitud_id}/estado")
def actualizar_estado(
    solicitud_id: UUID,
    datos: SolicitudEstadoActualizar
):
    try:
        return solicitud_service.cambiar_estado(
            solicitud_id,
            datos.estado,
            datos.observaciones
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/{solicitud_id}/validar")
def validar_documentos(solicitud_id: UUID):
    try:
        return solicitud_service.validar_documentos(solicitud_id)

    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al validar los documentos de la solicitud."
        )