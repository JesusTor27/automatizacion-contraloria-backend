
from app.repositories.solicitud_repository import solicitud_repository
from app.repositories.documento_repository import documento_repository
from app.repositories.envio_repository import envio_repository
from app.services.solicitud_service import solicitud_service
from app.supabase_client import supabase


BUCKET = "documentos-contraloria"


class EnvioService:

    def obtener_evidencia_aprobada(self, solicitud_id):

        # 1. Verificar que exista la solicitud
        solicitud = solicitud_repository.obtener_por_id(
            solicitud_id
        )

        if not solicitud:
            raise LookupError("La solicitud no existe.")

        # 2. Verificar que la evidencia esté aprobada
        if solicitud["estado"] != "EVIDENCIA_APROBADA":
            raise ValueError(
                "Solo se pueden enviar evidencias de solicitudes "
                "con estado EVIDENCIA_APROBADA."
            )

        # 3. Buscar los documentos registrados
        documentos = documento_repository.listar_por_solicitud(
            solicitud_id
        )

        evidencias_pdf = [
            documento
            for documento in documentos
            if documento["tipo"] == "EVIDENCIA_PDF"
        ]

        if not evidencias_pdf:
            raise ValueError(
                "No se encontró una evidencia PDF para esta solicitud."
            )

        # La lista viene ordenada por fecha_registro DESC
        documento = evidencias_pdf[0]

        # 4. Descargar el PDF desde Supabase Storage
        try:
            contenido = supabase.storage.from_(BUCKET).download(
                documento["ruta_almacenamiento"]
            )
        except Exception:
            raise RuntimeError(
                "No fue posible descargar la evidencia desde Storage."
            )

        if not contenido:
            raise ValueError(
                "El archivo PDF está vacío."
            )

        return {
            "solicitud_id": str(solicitud_id),
            "estado": solicitud["estado"],
            "documento": documento,
            "contenido": contenido
        }

    def confirmar_envio(
        self,
        solicitud_id,
        documento_id,
        destinatario,
        asunto,
        identificador_mensaje=None
    ):

        # 1. Verificar solicitud
        solicitud = solicitud_repository.obtener_por_id(
            solicitud_id
        )

        if not solicitud:
            raise LookupError("La solicitud no existe.")

        # 2. Verificar que esté aprobada
        if solicitud["estado"] != "EVIDENCIA_APROBADA":
            raise ValueError(
                "La solicitud no está aprobada o ya fue respondida."
            )

        # 3. Verificar los datos del envío
        if not destinatario or not destinatario.strip():
            raise ValueError(
                "Debe indicar el correo destinatario."
            )

        if not asunto or not asunto.strip():
            raise ValueError(
                "Debe indicar el asunto del correo."
            )

        # 4. Verificar que el documento pertenezca a la solicitud
        documentos = documento_repository.listar_por_solicitud(
            solicitud_id
        )

        evidencia = next(
            (
                documento
                for documento in documentos
                if str(documento["id"]) == str(documento_id)
                and documento["tipo"] == "EVIDENCIA_PDF"
            ),
            None
        )

        if not evidencia:
            raise ValueError(
                "El PDF indicado no pertenece a esta solicitud."
            )

        # 5. Verificar que sea la última evidencia generada
        ultima_evidencia = next(
            (
                documento
                for documento in documentos
                if documento["tipo"] == "EVIDENCIA_PDF"
            ),
            None
        )

        if not ultima_evidencia or str(
            ultima_evidencia["id"]
        ) != str(documento_id):
            raise ValueError(
                "El documento indicado no es la última evidencia generada."
            )

        # 6. Registrar el envío
        registro = envio_repository.crear({
            "solicitud_id": str(solicitud_id),
            "documento_id": str(documento_id),
            "destinatario": destinatario.strip(),
            "asunto": asunto.strip(),
            "identificador_mensaje": identificador_mensaje
        })

        # 7. Cambiar estado a RESPONDIDA
        solicitud_actualizada = solicitud_service.cambiar_estado(
            solicitud_id,
            "RESPONDIDA",
            "Evidencia enviada correctamente por correo electrónico."
        )

        return {
            "mensaje": "Envío registrado correctamente.",
            "envio": registro,
            "solicitud": solicitud_actualizada
        }

    def listar_envios(self, solicitud_id):

        solicitud = solicitud_repository.obtener_por_id(
            solicitud_id
        )

        if not solicitud:
            raise LookupError("La solicitud no existe.")

        return envio_repository.listar_por_solicitud(
            solicitud_id
        )


envio_service = EnvioService()
