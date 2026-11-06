
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No se encontró DATABASE_URL en el archivo .env")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

def verificar_conexion():
    with engine.connect() as connection:
        resultado = connection.execute(
            text("SELECT NOW()")
        )
        return resultado.scalar()
