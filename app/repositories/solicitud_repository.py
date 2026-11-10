from app.repositories.solicitud_repository import (
    solicitud_repository
)

from app.repositories.documento_repository import (
    documento_repository
)

from app.supabase_client import supabase


# ==========================================
# CONFIGURACIÓN
# ==========================================

ESTADOS_VALIDOS = {
    "RECIBIDA",
    "PENDIENTE",
    "LISTA_PARA_PUBLICAR",
    "PUBLICADA",
    "EVIDENCIA_GENERADA",
    "EVIDENCIA_APROBADA",
    "RESPONDIDA",
    "OBSERVADA"
}

BUCKET = "documentos-contraloria"

DOCUMENTOS_REQUERIDOS = {
    "DOCUMENTO_PUBLICAR",
    "FORMATO_PUBLICACION"
}


class SolicitudService:

    # ==========================================
    # CREAR SOLICITUD
    # ==========================================

    def crear_solicitud(self, datos):
        try:
            return solicitud_repository.crear(datos)

        except Exception as error:
            if "correo_message_id" in str(error):
                raise ValueError(
                    "Ya existe una solicitud asociada a ese correo."
                )

            raise

    # ==========================================
    # LISTAR SOLICITUDES
    # ==========================================

    def listar_solicitudes(self):
        return solicitud_repository.listar()

    # ==========================================
    # OBTENER SOLICITUD
    # ==========================================

    def obtener_solicitud(self, solicitud_id):
        solicitud = solicitud_repository.obtener_por_id(
            solicitud_id
        )

        if not solicitud:
            raise LookupError(
                "La solicitud no existe."
            )

        return solicitud

    # ==========================================
    # CONSULTAR HISTORIAL
    # ==========================================

    def obtener_historial(self, solicitud_id):
        # Verificar que la solicitud exista
        self.obtener_solicitud(solicitud_id)

        # Obtener todos sus cambios de estado
        return solicitud_repository.obtener_historial(
            solicitud_id
        )

    # ==========================================
    # CAMBIAR ESTADO
    # ==========================================

    def cambiar_estado(
        self,
        solicitud_id,
        nuevo_estado,
        observaciones=None
    ):
        if nuevo_estado not in ESTADOS_VALIDOS:
            raise ValueError(
                "El estado indicado no es válido."
            )

        solicitud = self.obtener_solicitud(
            solicitud_id
        )

        estado_anterior = solicitud["estado"]

        if estado_anterior != nuevo_estado:
            actualizada = (
                solicitud_repository.actualizar_estado(
                    solicitud_id,
                    nuevo_estado,
                    observaciones
                )
            )

            solicitud_repository.registrar_cambio_estado(
                solicitud_id,
                estado_anterior,
                nuevo_estado,
                observaciones or "Actualización de estado"
            )

            return actualizada

        return solicitud

    # ==========================================
    # VALIDAR DOCUMENTOS
    # ==========================================

    def validar_documentos(self, solicitud_id):
        solicitud = self.obtener_solicitud(
            solicitud_id
        )

        documentos = (
            documento_repository.listar_por_solicitud(
                solicitud_id
            )
        )

        tipos_encontrados = {
            documento["tipo"]
            for documento in documentos
        }

        documentos_faltantes = []
        archivos_faltantes_storage = []

        for tipo in DOCUMENTOS_REQUERIDOS:

            documentos_tipo = [
                documento
                for documento in documentos
                if documento["tipo"] == tipo
            ]

            if not documentos_tipo:
                documentos_faltantes.append(tipo)
                continue

            archivo_encontrado = False

            for documento in documentos_tipo:
                ruta = documento["ruta_almacenamiento"]

                carpeta, nombre_archivo = ruta.rsplit(
                    "/",
                    1
                )

                archivos = (
                    supabase.storage
                    .from_(BUCKET)
                    .list(carpeta)
                )

                existe = any(
                    archivo.get("name") == nombre_archivo
                    and not archivo.get(
                        "is_delete_marker",
                        False
                    )
                    for archivo in archivos
                )

                if existe:
                    archivo_encontrado = True
                    break

            if not archivo_encontrado:
                archivos_faltantes_storage.append(
                    tipo
                )

        # ==========================================
        # DETERMINAR ESTADO
        # ==========================================

        if (
            documentos_faltantes
            or archivos_faltantes_storage
        ):
            estado = "PENDIENTE"

            partes = []

            if documentos_faltantes:
                partes.append(
                    "Faltan documentos registrados: "
                    + ", ".join(
                        sorted(documentos_faltantes)
                    )
                )

            if archivos_faltantes_storage:
                partes.append(
                    "No se encontraron en Storage "
                    "los archivos de: "
                    + ", ".join(
                        sorted(
                            archivos_faltantes_storage
                        )
                    )
                )

            observaciones = ". ".join(
                partes
            )

        else:
            estado = "LISTA_PARA_PUBLICAR"

            observaciones = (
                "Los documentos obligatorios están "
                "registrados y existen en Supabase Storage."
            )

        # ==========================================
        # ACTUALIZAR ESTADO
        # ==========================================

        actualizada = self.cambiar_estado(
            solicitud_id,
            estado,
            observaciones
        )

        return {
            "solicitud_id": str(solicitud_id),
            "estado": estado,
            "documentos_registrados": sorted(
                tipos_encontrados
            ),
            "documentos_faltantes": sorted(
                documentos_faltantes
            ),
            "archivos_faltantes_storage": sorted(
                archivos_faltantes_storage
            ),
            "solicitud": actualizada
        }


# ==========================================
# INSTANCIA DEL SERVICIO
# ==========================================

solicitud_service = SolicitudService()
