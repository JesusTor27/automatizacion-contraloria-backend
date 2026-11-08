import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.services.evidencia_service import (
    generar_y_guardar_evidencia
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/evidencias",
    tags=["Evidencias"]
)


@router.post("/{solicitud_id}/generar")
def generar(solicitud_id: UUID):

    try:
        return generar_y_guardar_evidencia(solicitud_id)

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

        logger.exception(
            "Error al generar la evidencia de la solicitud %s",
            solicitud_id
        )

        raise HTTPException(
            status_code=500,
            detail="No fue posible generar la evidencia."
        ) from error
