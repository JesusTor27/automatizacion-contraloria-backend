from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from app.models.solicitud import (
    SolicitudCrear,
    SolicitudEstadoActualizar
)

from app.services.solicitud_service import solicitud_service
from app.security import verificar_usuario_supabase


# ==========================================
# CONFIGURACIÓN DEL ROUTER
# ==========================================

router = APIRouter(
    prefix="/solicitudes",
    tags=["Solicitudes"]
)


# ==========================================
# CREAR SOLICITUD
# ==========================================

@router.post("/")
def crear_solicitud(datos: SolicitudCrear):
    try:
        return solicitud_service.crear_solicitud(
            datos.model_dump(mode="json")
        )

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al registrar la solicitud."
        )


# ==========================================
# LISTAR SOLICITUDES
# ==========================================

@router.get("/")
def listar_solicitudes():
    try:
        return solicitud_service.listar_solicitudes()

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar las solicitudes."
        )


# ==========================================
# CONSULTAR HISTORIAL DE SOLICITUD
# ==========================================

@router.get("/{solicitud_id}/historial")
def obtener_historial_solicitud(
    solicitud_id: UUID,
    usuario: dict = Depends(verificar_usuario_supabase)
):
    try:
        historial = solicitud_service.obtener_historial(
            solicitud_id
        )

        return {
            "solicitud_id": str(solicitud_id),
            "total_eventos": len(historial),
            "historial": historial
        }

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No fue posible consultar el historial."
        )


# ==========================================
# OBTENER UNA SOLICITUD
# ==========================================

@router.get("/{solicitud_id}")
def obtener_solicitud(solicitud_id: UUID):
    try:
        return solicitud_service.obtener_solicitud(
            solicitud_id
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )


# ==========================================
# ACTUALIZAR ESTADO
# ==========================================

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
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# ==========================================
# VALIDAR DOCUMENTOS
# ==========================================


@router.post("/{solicitud_id}/validar")
def validar_documentos(solicitud_id: UUID):
    try:
        return solicitud_service.validar_documentos(
            solicitud_id
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        import logging

        logger = logging.getLogger(__name__)

        logger.exception(
            "Error al validar documentos de la solicitud %s",
            solicitud_id
        )

        raise HTTPException(
            status_code=500,
            detail="Error interno al validar los documentos."
        ) from error
