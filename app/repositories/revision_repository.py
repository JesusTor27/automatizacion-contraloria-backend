
from sqlalchemy import text
from app.database import engine


class RevisionRepository:

    def crear(self, datos):
        consulta = text("""
            INSERT INTO revisiones_evidencia (
                solicitud_id,
                estado_revision,
                responsable_revision,
                observaciones
            )
            VALUES (
                :solicitud_id,
                :estado_revision,
                :responsable_revision,
                :observaciones
            )
            RETURNING *
        """)

        with engine.begin() as connection:
            resultado = connection.execute(
                consulta,
                {
                    "solicitud_id": str(datos["solicitud_id"]),
                    "estado_revision": datos["estado_revision"],
                    "responsable_revision": datos["responsable_revision"],
                    "observaciones": datos.get("observaciones")
                }
            )

            return dict(resultado.mappings().one())

    def listar_por_solicitud(self, solicitud_id):
        consulta = text("""
            SELECT *
            FROM revisiones_evidencia
            WHERE solicitud_id = :solicitud_id
            ORDER BY fecha_revision DESC
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

    def obtener_ultima_revision(self, solicitud_id):
        consulta = text("""
            SELECT *
            FROM revisiones_evidencia
            WHERE solicitud_id = :solicitud_id
            ORDER BY fecha_revision DESC
            LIMIT 1
        """)

        with engine.connect() as connection:
            resultado = connection.execute(
                consulta,
                {"solicitud_id": str(solicitud_id)}
            )

            fila = resultado.mappings().first()

            return dict(fila) if fila else None


revision_repository = RevisionRepository()
