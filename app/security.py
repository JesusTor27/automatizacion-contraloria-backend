
import os
import secrets

from fastapi import Header, HTTPException
from dotenv import load_dotenv

load_dotenv()


def verificar_api_key(
    x_api_key: str = Header(default=None)
):
    clave_configurada = os.getenv("N8N_API_KEY")

    if not clave_configurada:
        raise HTTPException(
            status_code=500,
            detail="La clave de acceso no está configurada."
        )

    if not x_api_key or not secrets.compare_digest(
        x_api_key,
        clave_configurada
    ):
        raise HTTPException(
            status_code=401,
            detail="No autorizado."
        )

    return True
