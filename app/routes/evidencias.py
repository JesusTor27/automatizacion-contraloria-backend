
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.services.evidencia_service import (
    generar_y_guardar_evidencia
)


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
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No fue posible generar la evidencia."
        )
