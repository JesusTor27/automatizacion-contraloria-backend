
from sqlalchemy import text
from app.database import engine


class PublicacionRepository:

    def crear(self, datos):
        consulta = text("""
            INSERT INTO publicaciones (
                solicitud_id,
                fecha_publicacion,
                url_publicacion,
                responsable
            )
            VALUES (
                :solicitud_id,
                :fecha_publicacion,
                :url_publicacion,
                :responsable
            )
            RETURNING *
        """)

        with engine.begin() as connection:
            resultado = connection.execute(consulta, datos)
            return dict(resultado.mappings().one())

    def obtener_por_solicitud(self, solicitud_id):
        consulta = text("""
            SELECT *
            FROM publicaciones
            WHERE solicitud_id = :solicitud_id
        """)

        with engine.connect() as connection:
            resultado = connection.execute(
                consulta,
                {"solicitud_id": str(solicitud_id)}
            )

            fila = resultado.mappings().first()
            return dict(fila) if fila else None

    def actualizar(self, solicitud_id, datos):
        consulta = text("""
            UPDATE publicaciones
            SET
                fecha_publicacion = :fecha_publicacion,
                url_publicacion = :url_publicacion,
                responsable = :responsable
            WHERE solicitud_id = :solicitud_id
            RETURNING *
        """)

        parametros = {
            "solicitud_id": str(solicitud_id),
            "fecha_publicacion": datos["fecha_publicacion"],
            "url_publicacion": datos["url_publicacion"],
            "responsable": datos["responsable"]
        }

        with engine.begin() as connection:
            resultado = connection.execute(consulta, parametros)
            fila = resultado.mappings().first()

            return dict(fila) if fila else None

    def obtener_documentos_de_publicacion(self, solicitud_id):
        consulta = text("""
            SELECT *
            FROM documentos
            WHERE solicitud_id = :solicitud_id
            AND tipo = 'CAPTURA_PUBLICACION'
            ORDER BY fecha_registro DESC
            LIMIT 1
        """)

        with engine.connect() as connection:
            resultado = connection.execute(
                consulta,
                {"solicitud_id": str(solicitud_id)}
            )

            fila = resultado.mappings().first()
            return dict(fila) if fila else None


publicacion_repository = PublicacionRepository()
