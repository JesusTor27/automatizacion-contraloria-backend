import os
import uuid
from pathlib import Path

from app.supabase_client import supabase
from app.repositories.documento_repository import documento_repository
from app.repositories.solicitud_repository import solicitud_repository


BUCKET = "documentos-contraloria"
TAMANO_MAXIMO = 25 * 1024 * 1024  # 25 MB

TIPOS_PERMITIDOS = {
    ".pdf": ["application/pdf"],
    ".doc": ["application/msword"],
    ".docx": [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
}

TIPOS_DOCUMENTALES = [
    "DOCUMENTO_PUBLICAR",
    "FORMATO_PUBLICACION"
]


class DocumentoService:

    def cargar_documento(
        self,
        solicitud_id,
        tipo,
        nombre_archivo,
        tipo_mime,
        contenido
    ):
        # 1. Comprobar que la solicitud existe
        solicitud = solicitud_repository.obtener_por_id(
            solicitud_id
        )

        if not solicitud:
            raise LookupError(
                "La solicitud no existe."
            )

        # 2. Validar el tipo documental
        if tipo not in TIPOS_DOCUMENTALES:
            raise ValueError(
                "El tipo de documento no es válido."
            )

        # 3. Validar el tamaño
        if not contenido:
            raise ValueError(
                "El archivo está vacío."
            )

        if len(contenido) > TAMANO_MAXIMO:
            raise ValueError(
                "El archivo supera el límite de 25 MB."
            )

        # 4. Validar extensión y MIME
        extension = Path(nombre_archivo).suffix.lower()

        if extension not in TIPOS_PERMITIDOS:
            raise ValueError(
                "La extensión del archivo no está permitida."
            )

        if tipo_mime not in TIPOS_PERMITIDOS[extension]:
            raise ValueError(
                "El tipo de contenido del archivo no coincide."
            )

        # 5. Evitar nombres inseguros
        nombre_seguro = Path(nombre_archivo).name
        nombre_unico = f"{uuid.uuid4()}_{nombre_seguro}"

        ruta = (
            f"solicitudes/{solicitud_id}/"
            f"{tipo}/{nombre_unico}"
        )

        # 6. Subir a Supabase Storage
        try:
            supabase.storage.from_(BUCKET).upload(
                path=ruta,
                file=contenido,
                file_options={
                    "content-type": tipo_mime,
                    "upsert": "false"
                }
            )

            # 7. Registrar metadatos
            datos = {
                "solicitud_id": str(solicitud_id),
                "tipo": tipo,
                "nombre_archivo": nombre_seguro,
                "ruta_almacenamiento": ruta,
                "tipo_mime": tipo_mime
            }

            return documento_repository.crear(datos)

        except Exception:
            try:
                supabase.storage.from_(BUCKET).remove(
                    [ruta]
                )
            except Exception:
                pass

            raise

    def listar_documentos(self, solicitud_id):
        solicitud = solicitud_repository.obtener_por_id(
            solicitud_id
        )

        if not solicitud:
            raise LookupError(
                "La solicitud no existe."
            )

        return documento_repository.listar_por_solicitud(
            solicitud_id
        )

    def descargar_documento(self, documento_id):
        # 1. Buscar los metadatos en PostgreSQL
        documento = documento_repository.obtener_por_id(
            documento_id
        )

        if not documento:
            raise LookupError(
                "El documento no existe."
            )

        ruta = documento["ruta_almacenamiento"]

        if not ruta:
            raise ValueError(
                "El documento no tiene una ruta de almacenamiento."
            )

        # 2. Recuperar los bytes desde Supabase Storage
        contenido = supabase.storage.from_(
            BUCKET
        ).download(ruta)

        if not contenido:
            raise FileNotFoundError(
                "El archivo no está disponible en Supabase Storage."
            )

        # 3. Devolver el contenido y sus metadatos
        return {
            "contenido": bytes(contenido),
            "nombre_archivo": documento["nombre_archivo"],
            "tipo_mime": documento["tipo_mime"]
                or "application/octet-stream",
            "documento_id": str(documento["id"]),
            "solicitud_id": str(documento["solicitud_id"])
        }


documento_service = DocumentoService()
