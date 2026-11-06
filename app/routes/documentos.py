
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from uuid import UUID

from app.services.documento_service import documento_service


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
        raise HTTPException(status_code=404, detail=str(error))

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No fue posible cargar el documento."
        )

    finally:
        await archivo.close()


@router.get("/{solicitud_id}")
def listar_documentos(solicitud_id: UUID):
    try:
        return documento_service.listar_documentos(solicitud_id)

    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No fue posible consultar los documentos."
        )
