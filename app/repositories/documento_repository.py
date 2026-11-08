
from sqlalchemy import text
from app.database import engine


class DocumentoRepository:

    def crear(self, datos):
        consulta = text("""
            INSERT INTO documentos (
                solicitud_id,
                tipo,
                nombre_archivo,
                ruta_almacenamiento,
                tipo_mime
            )
            VALUES (
                :solicitud_id,
                :tipo,
                :nombre_archivo,
                :ruta_almacenamiento,
                :tipo_mime
            )
            RETURNING *
        """)

        with engine.begin() as connection:
            resultado = connection.execute(
                consulta,
                datos
            )

            return dict(
                resultado.mappings().one()
            )

    def listar_por_solicitud(self, solicitud_id):
        consulta = text("""
            SELECT *
            FROM documentos
            WHERE solicitud_id = :solicitud_id
            ORDER BY fecha_registro DESC
        """)

        with engine.connect() as connection:
            resultado = connection.execute(
                consulta,
                {"solicitud_id": str(solicitud_id)}
            )

            return [
                dict(fila)
                for fila in resultado.mappings()
            ]

    def obtener_por_id(self, documento_id):
        consulta = text("""
            SELECT *
            FROM documentos
            WHERE id = :documento_id
        """)

        with engine.connect() as connection:
            resultado = connection.execute(
                consulta,
                {"documento_id": str(documento_id)}
            )

            fila = resultado.mappings().first()

            return dict(fila) if fila else None


documento_repository = DocumentoRepository()
