from fastapi import FastAPI, HTTPException

from app.database import verificar_conexion
from app.supabase_client import supabase
from app.routes.solicitudes import router as solicitudes_router
from app.routes.documentos import router as documentos_router
from app.routes.publicaciones import router as publicaciones_router
from app.routes.evidencias import router as evidencias_router
from app.routes.revisiones import router as revisiones_router
from app.routes.envios import router as envios_router
from fastapi.middleware.cors import CORSMiddleware

# CONFIGURACIÓN DE LA API

app = FastAPI(
    title="Sistema de Automatización - Contraloría",
    description="API para gestionar solicitudes de publicación documental",
    version="1.0.0"
)

#Permitir trafico
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"]
)

# REGISTRO DE RUTAS

app.include_router(solicitudes_router)
app.include_router(documentos_router)
app.include_router(publicaciones_router)
app.include_router(evidencias_router)
app.include_router(revisiones_router)
app.include_router(envios_router)

# RUTA PRINCIPAL

@app.get("/")
def inicio():
    return {
        "mensaje": "API de automatización funcionando",
        "estado": "OK",
        "proyecto": "Contraloría - Automatización documental"
    }


# VERIFICACIÓN DE LA API


@app.get("/health", tags=["Sistema"])
def health():
    return {
        "estado": "API funcionando",
        "servicio": "FastAPI"
    }



# VERIFICACIÓN DE POSTGRESQL

@app.get("/db-check", tags=["Sistema"])
def db_check():
    try:
        fecha = verificar_conexion()

        return {
            "estado": "Conectado",
            "servidor": "Supabase PostgreSQL",
            "fecha_servidor": str(fecha)
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No fue posible conectar con PostgreSQL"
        )


# VERIFICACIÓN DE SUPABASE STORAGE

@app.get("/storage-check", tags=["Sistema"])
def storage_check():
    try:
        buckets = supabase.storage.list_buckets()
        nombres = [bucket.name for bucket in buckets]

        return {
            "estado": "Conectado",
            "buckets": nombres
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No fue posible consultar Supabase Storage"
        )
