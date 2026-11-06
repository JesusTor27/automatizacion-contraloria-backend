
from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.services.publicacion_service import publicacion_service


router = APIRouter(
    prefix="/publicaciones",
    tags=["Publicaciones"]
)


@router.post("/{solicitud_id}")
async def registrar_publicacion(
    solicitud_id: UUID,
    fecha_publicacion: date = Form(...),
    url_publicacion: str = Form(...),
    responsable: str = Form(...),
    captura: UploadFile = File(...)
):
    try:
        contenido = await captura.read()

        return publicacion_service.registrar_publicacion(
            solicitud_id=solicitud_id,
            fecha_publicacion=fecha_publicacion,
            url_publicacion=url_publicacion,
            responsable=responsable,
            nombre_archivo=captura.filename or "",
            tipo_mime=captura.content_type or "",
            contenido=contenido
        )

    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No fue posible registrar la publicación."
        )

    finally:
        await captura.close()


@router.put("/{solicitud_id}/corregir")
async def corregir_publicacion(
    solicitud_id: UUID,
    fecha_publicacion: date = Form(...),
    url_publicacion: str = Form(...),
    responsable: str = Form(...),
    captura: UploadFile = File(...)
):
    try:
        contenido = await captura.read()

        return publicacion_service.actualizar_publicacion(
            solicitud_id=solicitud_id,
            fecha_publicacion=fecha_publicacion,
            url_publicacion=url_publicacion,
            responsable=responsable,
            nombre_archivo=captura.filename or "",
            tipo_mime=captura.content_type or "",
            contenido=contenido
        )

    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No fue posible corregir la publicación."
        )

    finally:
        await captura.close()
