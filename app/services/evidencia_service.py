
import shutil
import subprocess
import uuid

from datetime import datetime, date
from pathlib import Path
from io import BytesIO

from docx import Document
from docx.shared import Inches
from PIL import Image

from app.repositories.solicitud_repository import solicitud_repository
from app.repositories.publicacion_repository import publicacion_repository
from app.repositories.documento_repository import documento_repository
from app.services.solicitud_service import solicitud_service
from app.supabase_client import supabase


# =========================================================
# CONFIGURACIÓN
# =========================================================

BUCKET = "documentos-contraloria"

BASE_DIR = Path(__file__).resolve().parents[2]

PLANTILLA = (
    BASE_DIR
    / "plantillas"
    / "plantilla_evidencia_publicacion.docx"
)

CARPETA_EVIDENCIAS = BASE_DIR / "evidencias"


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def formatear_fecha(valor):
    """Convierte fechas a formato DD/MM/YYYY."""

    if isinstance(valor, (datetime, date)):
        return valor.strftime("%d/%m/%Y")

    if valor:
        return str(valor)

    return "No especificada"


def reemplazar_texto(parrafo, valores):
    """Reemplaza los marcadores de la plantilla."""

    texto = parrafo.text

    for marcador, valor in valores.items():
        texto = texto.replace(marcador, str(valor))

    if texto != parrafo.text:
        parrafo.clear()
        parrafo.add_run(texto)


def recorrer_parrafos(documento):
    """Recorre párrafos normales y párrafos dentro de tablas."""

    for parrafo in documento.paragraphs:
        yield parrafo

    for tabla in documento.tables:
        for fila in tabla.rows:
            for celda in fila.cells:
                for parrafo in celda.paragraphs:
                    yield parrafo


def buscar_libreoffice():
    """Localiza el ejecutable de LibreOffice."""

    soffice = shutil.which("soffice")

    if soffice:
        return soffice

    posibles_rutas = [
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe")
    ]

    for ruta in posibles_rutas:
        if ruta.exists():
            return str(ruta)

    raise FileNotFoundError(
        "No se encontró LibreOffice. Verifica su instalación."
    )


# =========================================================
# GENERACIÓN DEL DOCUMENTO WORD Y PDF
# =========================================================

def generar_evidencia(
    solicitud_id,
    captura,
    fecha_publicacion=None,
    url_publicacion=None,
    nombre_funcionaria=None,
    observaciones=None,
    dependencia=None,
    version=1
):
    """
    Genera el documento DOCX y PDF de una publicación.

    captura: bytes de la imagen PNG o JPG.
    version: número de versión de la evidencia.
    """

    solicitud = solicitud_repository.obtener_por_id(solicitud_id)

    if not solicitud:
        raise LookupError("La solicitud no existe.")

    if not PLANTILLA.exists():
        raise FileNotFoundError(
            f"No se encontró la plantilla: {PLANTILLA}"
        )

    if not captura:
        raise ValueError("No se recibió ninguna captura.")

    try:
        imagen = Image.open(BytesIO(captura))
        imagen.verify()
    except Exception:
        raise ValueError("La captura no es una imagen válida.")

    CARPETA_EVIDENCIAS.mkdir(
        parents=True,
        exist_ok=True
    )

    identificador = uuid.uuid4().hex

    nombre_base = f"evidencia_v{version}_{identificador}"

    ruta_docx = CARPETA_EVIDENCIAS / f"{nombre_base}.docx"
    ruta_pdf = CARPETA_EVIDENCIAS / f"{nombre_base}.pdf"

    try:
        fecha_recepcion = formatear_fecha(
            solicitud["fecha_recepcion"]
        )

        valores = {
            "[CODIGO_SOLICITUD]": str(solicitud["id"]),
            "[CODIGO_PUBLICACION]": (
                solicitud.get("codigo_publicacion")
                or "No especificado"
            ),
            "[DEPENDENCIA]": dependencia or "No especificada",
            "[ASUNTO_DOCUMENTO]": (
                solicitud.get("asunto")
                or "No especificado"
            ),
            "[FECHA_RECEPCION]": fecha_recepcion,
            "[FECHA_PUBLICACION]": formatear_fecha(
                fecha_publicacion
            ),
            "[URL_PUBLICACION]": (
                url_publicacion or "No suministrada"
            ),
            "[NOMBRE_FUNCIONARIA]": (
                nombre_funcionaria or "Pendiente de completar"
            ),
            "[FECHA_VERIFICACION]": (
                datetime.now().strftime("%d/%m/%Y")
            ),
            "[PENDIENTE_REVISION / APROBADA / OBSERVADA]": (
                "PENDIENTE_REVISION"
            ),
            "[OBSERVACIONES]": (
                observaciones or "Sin observaciones."
            )
        }

        documento = Document(str(PLANTILLA))

        marcador_captura = (
            "[INSERTAR AQUÍ LA CAPTURA DE PANTALLA DE LA PUBLICACIÓN]"
        )

        captura_insertada = False

        for parrafo in recorrer_parrafos(documento):

            if marcador_captura in parrafo.text:
                parrafo.clear()

                parrafo.add_run().add_picture(
                    BytesIO(captura),
                    width=Inches(6.0)
                )

                captura_insertada = True

            else:
                reemplazar_texto(parrafo, valores)

        if not captura_insertada:
            raise ValueError(
                "No se encontró el espacio destinado a la captura "
                "en la plantilla."
            )

        documento.save(str(ruta_docx))

        soffice = buscar_libreoffice()

        resultado = subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(CARPETA_EVIDENCIAS),
                str(ruta_docx)
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        if resultado.returncode != 0 or not ruta_pdf.exists():
            raise RuntimeError(
                "No fue posible convertir el documento a PDF: "
                + resultado.stderr
            )

        return {
            "solicitud_id": str(solicitud_id),
            "version": version,
            "docx": str(ruta_docx),
            "pdf": str(ruta_pdf),
            "estado": "EVIDENCIA_GENERADA"
        }

    except Exception:
        for ruta in (ruta_docx, ruta_pdf):
            if ruta.exists():
                ruta.unlink()

        raise


# =========================================================
# GENERACIÓN Y ALMACENAMIENTO EN SUPABASE
# =========================================================

def generar_y_guardar_evidencia(solicitud_id):

    rutas_subidas = []

    try:
        # 1. Consultar solicitud
        solicitud = solicitud_repository.obtener_por_id(
            solicitud_id
        )

        if not solicitud:
            raise LookupError("La solicitud no existe.")

        estado_actual = solicitud["estado"]

        estados_permitidos = (
            "PUBLICADA",
            "LISTA_PARA_PUBLICAR",
            "OBSERVADA"
        )

        if estado_actual not in estados_permitidos:
            raise ValueError(
                "La solicitud debe estar en estado PUBLICADA, "
                "LISTA_PARA_PUBLICAR u OBSERVADA para generar "
                "una evidencia."
            )

        # 2. Consultar evidencias anteriores
        documentos_existentes = (
            documento_repository.listar_por_solicitud(
                solicitud_id
            )
        )

        # Calcular la siguiente versión según los DOCX registrados
        cantidad_versiones = sum(
            1
            for documento in documentos_existentes
            if documento["tipo"] == "EVIDENCIA_DOCX"
        )

        version = cantidad_versiones + 1

        # 3. Consultar datos de publicación
        publicacion = publicacion_repository.obtener_por_solicitud(
            solicitud_id
        )

        if not publicacion:
            raise ValueError(
                "No se encontraron los datos de publicación."
            )

        # 4. Consultar captura
        documento_captura = (
            publicacion_repository.obtener_documentos_de_publicacion(
                solicitud_id
            )
        )

        if not documento_captura:
            raise ValueError(
                "No se encontró la captura de publicación."
            )

        # 5. Descargar captura de Supabase Storage
        ruta_captura = documento_captura[
            "ruta_almacenamiento"
        ]

        captura = supabase.storage.from_(BUCKET).download(
            ruta_captura
        )

        # 6. Obtener dependencia
        dependencia = (
            solicitud_repository.obtener_nombre_dependencia(
                solicitud.get("dependencia_id")
            )
        )

        # 7. Generar DOCX y PDF de la versión correspondiente
        resultado = generar_evidencia(
            solicitud_id=solicitud_id,
            captura=captura,
            fecha_publicacion=publicacion[
                "fecha_publicacion"
            ],
            url_publicacion=publicacion[
                "url_publicacion"
            ],
            nombre_funcionaria=publicacion[
                "responsable"
            ],
            dependencia=dependencia,
            version=version
        )

        ruta_docx_local = Path(resultado["docx"])
        ruta_pdf_local = Path(resultado["pdf"])

        if not ruta_docx_local.exists():
            raise RuntimeError(
                "No se encontró el documento Word generado."
            )

        if not ruta_pdf_local.exists():
            raise RuntimeError(
                "No se encontró el documento PDF generado."
            )

        # 8. Preparar archivos
        archivos = [
            {
                "tipo": "EVIDENCIA_DOCX",
                "archivo": ruta_docx_local,
                "mime": (
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                )
            },
            {
                "tipo": "EVIDENCIA_PDF",
                "archivo": ruta_pdf_local,
                "mime": "application/pdf"
            }
        ]

        archivos_registrados = []

        # 9. Subir y registrar archivos
        for item in archivos:

            contenido = item["archivo"].read_bytes()

            nombre = (
                f"v{version}_{uuid.uuid4().hex}_"
                f"{item['archivo'].name}"
            )

            ruta = (
                f"solicitudes/{solicitud_id}/"
                f"{item['tipo']}/{nombre}"
            )

            supabase.storage.from_(BUCKET).upload(
                path=ruta,
                file=contenido,
                file_options={
                    "content-type": item["mime"],
                    "upsert": "false"
                }
            )

            rutas_subidas.append(ruta)

            registro = documento_repository.crear({
                "solicitud_id": str(solicitud_id),
                "tipo": item["tipo"],
                "nombre_archivo": item["archivo"].name,
                "ruta_almacenamiento": ruta,
                "tipo_mime": item["mime"]
            })

            archivos_registrados.append(registro)

        # 10. Actualizar a PUBLICADA si todavía no lo está
        if estado_actual == "LISTA_PARA_PUBLICAR":

            solicitud_service.cambiar_estado(
                solicitud_id,
                "PUBLICADA",
                "Publicación registrada y captura verificada."
            )

        # 11. Actualizar a EVIDENCIA_GENERADA
        solicitud_service.cambiar_estado(
            solicitud_id,
            "EVIDENCIA_GENERADA",
            (
                f"Evidencia versión {version} generada y "
                "almacenada correctamente. "
                "Pendiente de revisión."
            )
        )

        return {
            "mensaje": (
                "Evidencia generada y almacenada correctamente."
            ),
            "solicitud_id": str(solicitud_id),
            "version": version,
            "estado": "EVIDENCIA_GENERADA",
            "archivos": archivos_registrados
        }

    except Exception:

        # Eliminar archivos subidos a Storage si ocurre un error
        if rutas_subidas:
            try:
                supabase.storage.from_(BUCKET).remove(
                    rutas_subidas
                )
            except Exception:
                pass

        raise
