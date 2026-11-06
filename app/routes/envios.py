
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr

from app.services.envio_service import envio_service
from app.security import verificar_api_key


router = APIRouter(
    prefix="/envios",
    tags=["Envíos de correos"],
    dependencies=[Depends(verificar_api_key)]
)


class ConfirmarEnvioRequest(BaseModel):
    documento_id: UUID
    destinatario: EmailStr
    asunto: str
    identificador_mensaje: str | None = None


@router.get("/{solicitud_id}/evidencia")
def obtener_evidencia(solicitud_id: UUID):

    try:
        resultado = envio_service.obtener_evidencia_aprobada(
            solicitud_id
        )

        documento = resultado["documento"]

        return Response(
            content=resultado["contenido"],
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{documento["nombre_archivo"]}"'
                )
            }
        )

    except LookupError as error:
        raise HTTPException(404, detail=str(error))

    except ValueError as error:
        raise HTTPException(400, detail=str(error))

    except Exception:
        raise HTTPException(
            500,
            detail="No fue posible obtener la evidencia."
        )


@router.post("/{solicitud_id}/confirmar")
def confirmar_envio(
    solicitud_id: UUID,
    datos: ConfirmarEnvioRequest
):

    try:
        return envio_service.confirmar_envio(
            solicitud_id=solicitud_id,
            documento_id=datos.documento_id,
            destinatario=datos.destinatario,
            asunto=datos.asunto,
            identificador_mensaje=datos.identificador_mensaje
        )

    except LookupError as error:
        raise HTTPException(404, detail=str(error))

    except ValueError as error:
        raise HTTPException(400, detail=str(error))

    except Exception:
        raise HTTPException(
            500,
            detail="No fue posible registrar el envío."
        )


@router.get("/{solicitud_id}/historial")
def listar_envios(solicitud_id: UUID):

    try:
        return envio_service.listar_envios(solicitud_id)

    except LookupError as error:
        raise HTTPException(404, detail=str(error))

    except Exception:
        raise HTTPException(
            500,
            detail="No fue posible consultar el historial de envíos."
        )
