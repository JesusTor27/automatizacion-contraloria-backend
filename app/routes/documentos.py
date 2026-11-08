import logging
from uuid import UUID
from urllib.parse import quote
from app.security import verificar_acceso_documentos

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Form,
    Depends
)
from fastapi.responses import Response

from app.services.documento_service import documento_service
from app.security import verificar_api_key


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documentos",
    tags=["Documentos"]
)


@router.post("/cargar/{solicitud_id}")
async def cargar_documento(
    solicitud_id: UUID,
    tipo: str = Form(...),
    archivo: UploadFile = File(...)
):
    try:
        contenido = await archivo.read()

        return documento_service.cargar_documento(
            solicitud_id=solicitud_id,
            tipo=tipo,
            nombre_archivo=archivo.filename or "",
            tipo_mime=archivo.content_type or "",
            contenido=contenido
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
        logger.exception(
            "Error al cargar documento de solicitud %s",
            solicitud_id
        )

        raise HTTPException(
            status_code=500,
            detail="No fue posible cargar el documento."
        ) from error

    finally:
        await archivo.close()


@router.get("/archivo/{documento_id}")
def descargar_documento(
    documento_id: UUID,
    _: bool = Depends(verificar_acceso_documentos)
):
    try:
        archivo = documento_service.descargar_documento(
            documento_id
        )

        nombre_codificado = quote(
            archivo["nombre_archivo"],
            safe=""
        )

        return Response(
            content=archivo["contenido"],
            media_type=archivo["tipo_mime"],
            headers={
                "Content-Disposition": (
                    "attachment; filename=\"documento\"; "
                    f"filename*=UTF-8''{nombre_codificado}"
                ),
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "no-store"
            }
        )

    except (LookupError, FileNotFoundError) as error:
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
            "Error al descargar documento %s",
            documento_id
        )

        raise HTTPException(
            status_code=500,
            detail="No fue posible descargar el documento."
        ) from error


@router.get("/{solicitud_id}")
def listar_documentos(solicitud_id: UUID):
    try:
        return documento_service.listar_documentos(
            solicitud_id
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        ) from error

    except Exception as error:
        logger.exception(
            "Error al consultar documentos de solicitud %s",
            solicitud_id
        )

        raise HTTPException(
            status_code=500,
            detail="No fue posible consultar los documentos."
        ) from error
