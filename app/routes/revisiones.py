
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.revision_service import revision_service


router = APIRouter(
    prefix="/revisiones",
    tags=["Revisiones de evidencias"]
)


class RevisionRequest(BaseModel):
    responsable_revision: str
    observaciones: str | None = None


@router.post("/{solicitud_id}/aprobar")
def aprobar_evidencia(
    solicitud_id: str,
    datos: RevisionRequest
):
    try:
        return revision_service.revisar_evidencia(
            solicitud_id=solicitud_id,
            estado_revision="APROBADA",
            responsable_revision=datos.responsable_revision,
            observaciones=datos.observaciones
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error al aprobar la evidencia: {str(error)}"
        )


@router.post("/{solicitud_id}/observar")
def observar_evidencia(
    solicitud_id: str,
    datos: RevisionRequest
):
    try:
        return revision_service.revisar_evidencia(
            solicitud_id=solicitud_id,
            estado_revision="OBSERVADA",
            responsable_revision=datos.responsable_revision,
            observaciones=datos.observaciones
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error al observar la evidencia: {str(error)}"
        )
