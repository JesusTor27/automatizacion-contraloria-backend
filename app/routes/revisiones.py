
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.revision_service import revision_service
from app.security import verificar_usuario_supabase


router = APIRouter(
    prefix="/revisiones",
    tags=["Revisiones de evidencias"]
)


class RevisionRequest(BaseModel):
    observaciones: str | None = None


@router.post("/{solicitud_id}/aprobar")
def aprobar_evidencia(
    solicitud_id: str,
    datos: RevisionRequest,
    usuario: dict = Depends(verificar_usuario_supabase)
):
    try:
        responsable = usuario.get("email") or usuario["id"]

        return revision_service.revisar_evidencia(
            solicitud_id=solicitud_id,
            estado_revision="APROBADA",
            responsable_revision=responsable,
            observaciones=datos.observaciones
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No fue posible aprobar la evidencia."
        )


@router.post("/{solicitud_id}/observar")
def observar_evidencia(
    solicitud_id: str,
    datos: RevisionRequest,
    usuario: dict = Depends(verificar_usuario_supabase)
):
    observaciones = (datos.observaciones or "").strip()

    if not observaciones:
        raise HTTPException(
            status_code=422,
            detail="Debes escribir el motivo de la observación."
        )

    try:
        responsable = usuario.get("email") or usuario["id"]

        return revision_service.revisar_evidencia(
            solicitud_id=solicitud_id,
            estado_revision="OBSERVADA",
            responsable_revision=responsable,
            observaciones=observaciones
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No fue posible registrar la observación."
        )
