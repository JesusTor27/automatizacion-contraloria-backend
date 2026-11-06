
from fastapi import HTTPException

from app.repositories.revision_repository import revision_repository
from app.repositories.solicitud_repository import solicitud_repository
from app.services.solicitud_service import solicitud_service


class RevisionService:

    def revisar_evidencia(
        self,
        solicitud_id,
        estado_revision,
        responsable_revision,
        observaciones=None
    ):
        # Validar el resultado de la revisión
        if estado_revision not in ["APROBADA", "OBSERVADA"]:
            raise HTTPException(
                status_code=400,
                detail="El resultado debe ser APROBADA u OBSERVADA."
            )

        # Validar el responsable
        if not responsable_revision or not responsable_revision.strip():
            raise HTTPException(
                status_code=400,
                detail="Debe indicar quién realiza la revisión."
            )

        # Una observación debe incluir una explicación
        if estado_revision == "OBSERVADA":
            if not observaciones or not observaciones.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Debe indicar las observaciones o correcciones solicitadas."
                )

        # Consultar solicitud
        solicitud = solicitud_repository.obtener_por_id(solicitud_id)

        if not solicitud:
            raise HTTPException(
                status_code=404,
                detail="La solicitud no existe."
            )

        # Solo se pueden revisar evidencias generadas
        if solicitud["estado"] != "EVIDENCIA_GENERADA":
            raise HTTPException(
                status_code=400,
                detail=(
                    "La solicitud debe estar en estado "
                    "EVIDENCIA_GENERADA para realizar la revisión."
                )
            )

        # Determinar el nuevo estado de la solicitud
        nuevo_estado = (
            "EVIDENCIA_APROBADA"
            if estado_revision == "APROBADA"
            else "OBSERVADA"
        )

        # Registrar la revisión
        revision = revision_repository.crear({
            "solicitud_id": solicitud_id,
            "estado_revision": estado_revision,
            "responsable_revision": responsable_revision.strip(),
            "observaciones": observaciones.strip() if observaciones else None
        })

        # Actualizar estado e historial
        solicitud_actualizada = solicitud_service.cambiar_estado(
            solicitud_id,
            nuevo_estado,
            observaciones
        )

        return {
            "mensaje": (
                "Evidencia aprobada correctamente."
                if estado_revision == "APROBADA"
                else "Evidencia observada. Se requieren correcciones."
            ),
            "revision": revision,
            "solicitud": solicitud_actualizada
        }


revision_service = RevisionService()
