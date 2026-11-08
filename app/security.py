
import os
import secrets

from fastapi import Header, HTTPException
from dotenv import load_dotenv

from app.supabase_client import supabase

load_dotenv()


# ==========================================
# AUTENTICACIÓN PARA N8N
# ==========================================

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


# ==========================================
# AUTENTICACIÓN PARA EL FRONTEND
# ==========================================

def verificar_usuario_supabase(
    authorization: str = Header(default=None)
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión para acceder."
        )

    esquema, separador, token = authorization.partition(" ")

    if (
        not separador
        or esquema.lower() != "bearer"
        or not token.strip()
    ):
        raise HTTPException(
            status_code=401,
            detail="Formato de autorización inválido."
        )

    token = token.strip()

    try:
        # Supabase valida el token y recupera al usuario
        respuesta = supabase.auth.get_user(token)

        usuario = respuesta.user

        if not usuario or not usuario.id:
            raise HTTPException(
                status_code=401,
                detail="Usuario no autorizado."
            )

        return {
            "id": usuario.id,
            "email": usuario.email,
            "autenticado": True
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o sesión expirada."
        )
