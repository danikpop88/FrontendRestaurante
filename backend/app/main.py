"""
main.py — Punto ÚNICO de ensamblaje de la API.

PAPEL EN LA ARQUITECTURA: es el único archivo que conoce las clases concretas
y las arma (Artículo 5 de la constitución). Si mañana cambia el reloj, el
motor de base de datos o el servicio de pago, solo cambia este archivo.

En esta fase hace tres cosas:
  1. Crea la aplicación FastAPI y el gestor de sesiones (con el reloj real).
  2. Activa CORS únicamente para el origen del front (ORIGEN_FRONT).
  3. Registra los manejadores que traducen cada excepción de negocio a su
     código HTTP (Plan §5.10), siempre con la envoltura de error de los
     Contratos §0:  {"estado": 409, "mensaje": "...", "errores": []}

Los módulos de negocio (autenticación, menú, pedidos...) se irán registrando
aquí, fase por fase, con app.include_router(...).

Cómo arrancarla (desde la carpeta backend/):
    uvicorn app.main:app --port 8000
La documentación automática queda en http://localhost:8000/docs
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config
from app.compartido.excepciones import (
    NoAutenticadoError,
    NoEncontradoError,
    ReglaNegocioError,
    SinPermisoError,
)
from app.compartido.reloj import RelojSistema
from app.compartido.seguridad import GestorSesiones

registro = logging.getLogger("mesa_abuela")

app = FastAPI(title="La mesa de la abuela")

# --- Ensamblaje de las dependencias concretas -------------------------------
reloj = RelojSistema()
app.state.sesiones = GestorSesiones(reloj)

# --- CORS: solo el origen del front puede llamar a la API (Artículo 11) -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.ORIGEN_FRONT],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# --- Traducción de errores a HTTP (Plan §5.10) -------------------------------
def _respuesta_error(estado: int, mensaje: str, errores: list[str] | None = None) -> JSONResponse:
    """Arma la envoltura de error de los Contratos §0."""
    return JSONResponse(
        status_code=estado,
        content={"estado": estado, "mensaje": mensaje, "errores": errores or []},
    )


# Excepción de negocio -> código HTTP. El mensaje es el que lanzó el servicio.
_CODIGOS = {
    NoAutenticadoError: 401,
    SinPermisoError: 403,
    NoEncontradoError: 404,
    ReglaNegocioError: 409,
}


def _crear_manejador(codigo: int):
    async def manejador(request: Request, error: Exception) -> JSONResponse:
        return _respuesta_error(codigo, str(error))
    return manejador


for _clase, _codigo in _CODIGOS.items():
    app.add_exception_handler(_clase, _crear_manejador(_codigo))


@app.exception_handler(RequestValidationError)
async def manejar_validacion(request: Request, error: RequestValidationError) -> JSONResponse:
    """Datos con forma inválida (tipo, campo faltante o vacío): 422 con la lista de errores."""
    errores = []
    for detalle in error.errors():
        # El último elemento de 'loc' es el nombre del campo (ej. "email").
        campo = str(detalle["loc"][-1]) if detalle["loc"] else "datos"
        if detalle["type"] == "missing":
            errores.append(f"El campo '{campo}' es obligatorio.")
        elif detalle["type"] == "value_error":
            # Mensaje propio (ej. clave corta); se quita el prefijo en inglés.
            errores.append(str(detalle["msg"]).removeprefix("Value error, "))
        else:
            errores.append(f"El campo '{campo}' no es válido.")
    return _respuesta_error(422, "Los datos enviados no son válidos.", errores)


@app.exception_handler(Exception)
async def manejar_error_inesperado(request: Request, error: Exception) -> JSONResponse:
    """Cualquier otro error: 500 genérico. El detalle queda en el registro, no en la respuesta."""
    registro.exception("Error inesperado en %s", request.url.path)
    return _respuesta_error(500, "Ocurrió un error inesperado. Intente de nuevo más tarde.")


# --- Aquí se registrarán los módulos, fase por fase -------------------------
# Fase 2: app.include_router(rutas_autenticacion.router)