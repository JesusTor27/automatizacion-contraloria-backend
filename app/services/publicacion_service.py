
from datetime import date
from urllib.parse import urlparse
from pathlib import Path
from uuid import uuid4
from io import BytesIO

from PIL import Image

from app.supabase_client import supabase
from app.repositories.solicitud_repository import solicitud_repository
from app.repositories.publicacion_repository import publicacion_repository
from app.repositories.documento_repository import documento_repository


BUCKET = "documentos-contraloria"
TAMANO_MAXIMO = 10 * 1024 * 1024  # 10 MB

IMAGENES_PERMITIDAS = {
    "image/png": ".png",
    "image/jpeg": ".jpg"
}


class PublicacionService:

    def _validar_datos(
        self,
        fecha_publicacion,
        url_publicacion,
        responsable,
        tipo_mime,
        contenido
    ):
        if not responsable or not responsable.strip():
            raise ValueError("Debe indicar el nombre del responsable.")

        url = urlparse(url_publicacion.strip())

        if url.scheme != "https" or not url.netloc:
            raise ValueError("Debe proporcionar una URL HTTPS válida.")

        if fecha_publicacion > date.today():
            raise ValueError(
                "La fecha de publicación no puede ser futura."
            )

        if tipo_mime not in IMAGENES_PERMITIDAS:
            raise ValueError("La captura debe ser PNG o JPG.")

        if not contenido:
            raise ValueError("No se recibió la captura.")

        if len(contenido) > TAMANO_MAXIMO:
            raise ValueError("La captura supera el límite de 10 MB.")

        try:
            imagen = Image.open(BytesIO(contenido))
            imagen.verify()
        except Exception:
            raise ValueError("El archivo recibido no es una imagen válida.")

    def _subir_captura(self, solicitud_id, tipo_mime, contenido):
        extension = IMAGENES_PERMITIDAS[tipo_mime]
        nombre_unico = f"{uuid4()}{extension}"

        ruta = (
            f"solicitudes/{solicitud_id}/CAPTURA_PUBLICACION/"
            f"{nombre_unico}"
        )

        supabase.storage.from_(BUCKET).upload(
            path=ruta,
            file=contenido,
            file_options={
                "content-type": tipo_mime,
                "upsert": "false"
            }
        )

        return ruta

    def registrar_publicacion(
        self,
        solicitud_id,
        fecha_publicacion,
        url_publicacion,
        responsable,
        nombre_archivo,
        tipo_mime,
        contenido
    ):
        # 1. Verificar solicitud
        solicitud = solicitud_repository.obtener_por_id(solicitud_id)

        if not solicitud:
            raise LookupError("La solicitud no existe.")

        if solicitud["estado"] != "LISTA_PARA_PUBLICAR":
            raise ValueError(
                "La solicitud debe estar lista para publicar."
            )

        # 2. Evitar publicaciones duplicadas
        existente = publicacion_repository.obtener_por_solicitud(
            solicitud_id
        )

        if existente:
            raise ValueError(
                "Esta solicitud ya tiene una publicación registrada."
            )

        # 3. Validar información y captura
        self._validar_datos(
            fecha_publicacion,
            url_publicacion,
            responsable,
            tipo_mime,
            contenido
        )

        # 4. Subir captura
        ruta = self._subir_captura(
            solicitud_id,
            tipo_mime,
            contenido
        )

        try:
            # 5. Registrar publicación
            publicacion = publicacion_repository.crear({
                "solicitud_id": str(solicitud_id),
                "fecha_publicacion": fecha_publicacion,
                "url_publicacion": url_publicacion.strip(),
                "responsable": responsable.strip()
            })

            # 6. Registrar captura
            documento = documento_repository.crear({
                "solicitud_id": str(solicitud_id),
                "tipo": "CAPTURA_PUBLICACION",
                "nombre_archivo": Path(nombre_archivo).name,
                "ruta_almacenamiento": ruta,
                "tipo_mime": tipo_mime
            })

            return {
                "mensaje": "Datos de publicación registrados correctamente.",
                "publicacion": publicacion,
                "captura": documento
            }

        except Exception:
            try:
                supabase.storage.from_(BUCKET).remove([ruta])
            except Exception:
                pass

            raise

    def actualizar_publicacion(
        self,
        solicitud_id,
        fecha_publicacion,
        url_publicacion,
        responsable,
        nombre_archivo,
        tipo_mime,
        contenido
    ):
        # 1. Verificar solicitud
        solicitud = solicitud_repository.obtener_por_id(solicitud_id)

        if not solicitud:
            raise LookupError("La solicitud no existe.")

        # 2. Solo permitir correcciones de solicitudes observadas
        if solicitud["estado"] != "OBSERVADA":
            raise ValueError(
                "Solo se pueden corregir publicaciones de solicitudes observadas."
            )

        # 3. Verificar que ya exista una publicación registrada
        publicacion_existente = (
            publicacion_repository.obtener_por_solicitud(solicitud_id)
        )

        if not publicacion_existente:
            raise ValueError(
                "No existe una publicación registrada para corregir."
            )

        # 4. Validar los nuevos datos
        self._validar_datos(
            fecha_publicacion,
            url_publicacion,
            responsable,
            tipo_mime,
            contenido
        )

        # 5. Subir la nueva captura
        ruta = self._subir_captura(
            solicitud_id,
            tipo_mime,
            contenido
        )

        try:
            # 6. Actualizar los datos de la publicación existente
            publicacion = publicacion_repository.actualizar(
                solicitud_id,
                {
                    "fecha_publicacion": fecha_publicacion,
                    "url_publicacion": url_publicacion.strip(),
                    "responsable": responsable.strip()
                }
            )

            if not publicacion:
                raise ValueError(
                    "No fue posible actualizar los datos de la publicación."
                )

            # 7. Registrar la nueva captura sin eliminar la anterior
            documento = documento_repository.crear({
                "solicitud_id": str(solicitud_id),
                "tipo": "CAPTURA_PUBLICACION",
                "nombre_archivo": Path(nombre_archivo).name,
                "ruta_almacenamiento": ruta,
                "tipo_mime": tipo_mime
            })

            return {
                "mensaje": "Publicación corregida correctamente. Ya puedes generar una nueva evidencia.",
                "publicacion": publicacion,
                "captura": documento
            }

        except Exception:
            # Si ocurre un error, retirar el nuevo archivo de Storage.
            # Las capturas anteriores se conservan.
            try:
                supabase.storage.from_(BUCKET).remove([ruta])
            except Exception:
                pass

            raise


publicacion_service = PublicacionService()
