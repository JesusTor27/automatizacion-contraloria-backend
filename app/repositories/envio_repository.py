
from sqlalchemy import text
from app.database import engine


class EnvioRepository:

    def crear(self, datos):
        consulta = text("""
            INSERT INTO envios_correo (
                solicitud_id,
                documento_id,
                destinatario,
                asunto,
                identificador_mensaje
            )
            VALUES (
                :solicitud_id,
                :documento_id,
                :destinatario,
                :asunto,
                :identificador_mensaje
            )
            RETURNING *
        """)

        with engine.begin() as connection:
            resultado = connection.execute(
                consulta,
                {
                    "solicitud_id": str(datos["solicitud_id"]),
                    "documento_id": str(datos["documento_id"]),
                    "destinatario": datos["destinatario"],
                    "asunto": datos["asunto"],
                    "identificador_mensaje": datos.get(
                        "identificador_mensaje"
                    )
                }
            )

            return dict(resultado.mappings().one())

    def listar_por_solicitud(self, solicitud_id):
        consulta = text("""
            SELECT *
            FROM envios_correo
            WHERE solicitud_id = :solicitud_id
            ORDER BY fecha_envio DESC
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


envio_repository = EnvioRepository()
