from sqlalchemy import text
from app.database import engine


class SolicitudRepository:

    # ==========================================
    # CREAR SOLICITUD
    # ==========================================

    def crear(self, datos):
        consulta = text("""
            INSERT INTO solicitudes (
                asunto,
                remitente,
                dependencia_id,
                correo_message_id,
                codigo_publicacion
            )
            VALUES (
                :asunto,
                :remitente,
                :dependencia_id,
                :correo_message_id,
                :codigo_publicacion
            )
            RETURNING *
        """)

        with engine.begin() as connection:
            resultado = connection.execute(
                consulta,
                datos
            )

            return dict(resultado.mappings().one())

    # ==========================================
    # LISTAR SOLICITUDES
    # ==========================================

    def listar(self):
        consulta = text("""
            SELECT *
            FROM solicitudes
            ORDER BY fecha_recepcion DESC
        """)

        with engine.connect() as connection:
            resultado = connection.execute(consulta)

            return [
                dict(fila)
                for fila in resultado.mappings()
            ]

    # ==========================================
    # OBTENER SOLICITUD POR ID
    # ==========================================

    def obtener_por_id(self, solicitud_id):
        consulta = text("""
            SELECT *
            FROM solicitudes
            WHERE id = :id
        """)

        with engine.connect() as connection:
            resultado = connection.execute(
                consulta,
                {"id": str(solicitud_id)}
            )

            fila = resultado.mappings().first()

            return dict(fila) if fila else None

    # ==========================================
    # ACTUALIZAR ESTADO
    # ==========================================

    def actualizar_estado(
        self,
        solicitud_id,
        estado,
        observaciones
    ):
        consulta = text("""
            UPDATE solicitudes
            SET
                estado = :estado,
                observaciones = :observaciones,
                updated_at = NOW()
            WHERE id = :id
            RETURNING *
        """)

        with engine.begin() as connection:
            resultado = connection.execute(
                consulta,
                {
                    "id": str(solicitud_id),
                    "estado": estado,
                    "observaciones": observaciones
                }
            )

            fila = resultado.mappings().first()

            return dict(fila) if fila else None

    # ==========================================
    # OBTENER TIPOS DE DOCUMENTOS
    # ==========================================

    def obtener_tipos_documentos(self, solicitud_id):
        consulta = text("""
            SELECT tipo
            FROM documentos
            WHERE solicitud_id = :id
        """)

        with engine.connect() as connection:
            resultado = connection.execute(
                consulta,
                {"id": str(solicitud_id)}
            )

            return [
                fila.tipo
                for fila in resultado
            ]

    # ==========================================
    # REGISTRAR CAMBIO DE ESTADO
    # ==========================================

    def registrar_cambio_estado(
        self,
        solicitud_id,
        estado_anterior,
        estado_nuevo,
        detalle
    ):
        consulta = text("""
            INSERT INTO historial_estados (
                solicitud_id,
                estado_anterior,
                estado_nuevo,
                detalle
            )
            VALUES (
                :solicitud_id,
                :estado_anterior,
                :estado_nuevo,
                :detalle
            )
        """)

        with engine.begin() as connection:
            connection.execute(
                consulta,
                {
                    "solicitud_id": str(solicitud_id),
                    "estado_anterior": estado_anterior,
                    "estado_nuevo": estado_nuevo,
                    "detalle": detalle
                }
            )

    # ==========================================
    # CONSULTAR HISTORIAL DE SOLICITUD
    # ==========================================

    def obtener_historial(self, solicitud_id):
        consulta = text("""
            SELECT *
            FROM historial_estados
            WHERE solicitud_id = :solicitud_id
        """)

        with engine.connect() as connection:
            resultado = connection.execute(
                consulta,
                {
                    "solicitud_id": str(solicitud_id)
                }
            )

            registros = [
                dict(fila)
                for fila in resultado.mappings()
            ]

        # Ordenar por el campo de fecha disponible.
        # Se contemplan varios nombres habituales.
        def obtener_fecha(registro):
            for campo in (
                "fecha_cambio",
                "fecha_registro",
                "created_at"
            ):
                valor = registro.get(campo)

                if valor is not None:
                    return str(valor)

            return ""

        registros.sort(key=obtener_fecha)

        return registros

    # ==========================================
    # OBTENER NOMBRE DE DEPENDENCIA
    # ==========================================

    def obtener_nombre_dependencia(self, dependencia_id):
        if not dependencia_id:
            return None

        consulta = text("""
            SELECT nombre
            FROM dependencias
            WHERE id = :dependencia_id
        """)

        with engine.connect() as connection:
            resultado = connection.execute(
                consulta,
                {
                    "dependencia_id": str(dependencia_id)
                }
            )

            fila = resultado.mappings().first()

            return fila["nombre"] if fila else None


# ==========================================
# INSTANCIA DEL REPOSITORIO
# ==========================================

solicitud_repository = SolicitudRepository()
