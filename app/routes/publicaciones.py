
from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Form,
    Depends
)

from app.services.publicacion_service import publicacion_service
from app.repositories.publicacion_repository import publicacion_repository
from app.security import verificar_usuario_supabase


router = APIRouter(
    prefix="/publicaciones",
    tags=["Publicaciones"]
)


# ==========================================
# CONSULTAR PUBLICACIÓN
# ==========================================

@router.get("/{solicitud_id}")
def consultar_publicacion(
    solicitud_id: UUID,
    usuario: dict = Depends(verificar_usuario_supabase)
):
    publicacion = publicacion_repository.obtener_por_solicitud(
        solicitud_id
    )

    if not publicacion:
        raise HTTPException(
            status_code=404,
            detail="No existe una publicación registrada."
        )

    return publicacion


# ==========================================
# REGISTRAR PUBLICACIÓN
# ==========================================

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
            detail="No fue posible registrar la publicación."
        )

    finally:
        await captura.close()


# ==========================================
# CORREGIR PUBLICACIÓN RECHAZADA
# ==========================================

@router.put("/{solicitud_id}/corregir")
async def corregir_publicacion(
    solicitud_id: UUID,
    fecha_publicacion: date = Form(...),
    url_publicacion: str = Form(...),
    responsable: str = Form(...),
    captura: UploadFile = File(...),
    usuario: dict = Depends(verificar_usuario_supabase)
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
            detail="No fue posible corregir la publicación."
        )

    finally:
        await captura.close()
