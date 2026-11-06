
from sqlalchemy import text
from app.database import engine


class SolicitudRepository:

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

    def listar(self):
        consulta = text("""
            SELECT *
            FROM solicitudes
            ORDER BY fecha_recepcion DESC
        """)

        with engine.connect() as connection:
            resultado = connection.execute(consulta)
            return [dict(fila) for fila in resultado.mappings()]

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

    def actualizar_estado(self, solicitud_id, estado, observaciones):
        consulta = text("""
            UPDATE solicitudes
            SET estado = :estado,
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
            return [fila.tipo for fila in resultado]

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
                {"dependencia_id": str(dependencia_id)}
            )

            fila = resultado.mappings().first()

            return fila["nombre"] if fila else None        


solicitud_repository = SolicitudRepository()
