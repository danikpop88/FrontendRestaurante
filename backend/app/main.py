"""
main.py — Punto ÚNICO de ensamblaje de la API.

PAPEL EN LA ARQUITECTURA: es el único archivo que conoce las clases concretas
y las arma (Artículo 5 de la constitución). Si mañana cambia el reloj, el
motor de base de datos o el servicio de pago, solo cambia este archivo.

Hace cuatro cosas:
  1. Crea la aplicación FastAPI y el gestor de sesiones (con el reloj real).
  2. Activa CORS únicamente para el origen del front (ORIGEN_FRONT).
  3. Registra los manejadores que traducen cada excepción de negocio a su
     código HTTP (Plan §5.10), siempre con la envoltura de error de los
     Contratos §0:  {"estado": 409, "mensaje": "...", "errores": []}
  4. Ensambla cada módulo de negocio y registra sus rutas.

Cómo arrancarla (desde la carpeta backend/):
    uvicorn app.main:app --port 8000
La documentación automática queda en http://localhost:8000/docs
"""

import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config
from app.autenticacion import rutas as rutas_autenticacion
from app.autenticacion.modelos import Administrador, Domiciliario, Mesero
from app.autenticacion.repositorio_postgres import RepositorioUsuariosPostgres
from app.autenticacion.servicio import GestorAutenticacion
from app.compartido.conexion import obtener_conexion
from app.compartido.excepciones import (
    NoAutenticadoError,
    NoEncontradoError,
    ReglaNegocioError,
    SinPermisoError,
    ValidacionError,
)
from app.menu import rutas as rutas_menu
from app.menu.repositorio_postgres import RepositorioProductosPostgres
from app.menu.servicio import GestorMenu
from app.compartido.reloj import RelojSistema
from app.compartido.seguridad import GestorSesiones

registro = logging.getLogger("mesa_abuela")

app = FastAPI(title="La mesa de la abuela")

# --- Ensamblaje de las dependencias concretas -------------------------------
reloj = RelojSistema()
app.state.sesiones = GestorSesiones(reloj)

# Qué clase de empleado corresponde a cada tipo_cargo. El Chef se sumará aquí
# en la Fase 7, cuando exista su clase.
CLASES_EMPLEADO = {
    "Mesero": Mesero,
    "Domiciliario": Domiciliario,
    "Administrador": Administrador,
}

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

@app.exception_handler(ValidacionError)
async def manejar_validacion_negocio(request: Request, error: ValidacionError) -> JSONResponse:
    """Validación de negocio (nombre vacío, precio negativo, categoría inexistente): 422 con los motivos."""
    return _respuesta_error(422, str(error), error.errores)

@app.exception_handler(Exception)
async def manejar_error_inesperado(request: Request, error: Exception) -> JSONResponse:
    """Cualquier otro error: 500 genérico. El detalle queda en el registro, no en la respuesta."""
    registro.exception("Error inesperado en %s", request.url.path)
    return _respuesta_error(500, "Ocurrió un error inesperado. Intente de nuevo más tarde.")


# --- Módulo: Autenticación de usuarios (Fase 2) -----------------------------
def _gestor_autenticacion(conexion=Depends(obtener_conexion)) -> GestorAutenticacion:
    """Arma el gestor con la conexión de ESTA petición (una conexión por petición)."""
    repositorio = RepositorioUsuariosPostgres(conexion, CLASES_EMPLEADO)
    return GestorAutenticacion(repositorio, app.state.sesiones, CLASES_EMPLEADO)


app.include_router(rutas_autenticacion.router)
app.dependency_overrides[rutas_autenticacion.obtener_gestor] = _gestor_autenticacion


# --- Módulo: Menú y productos (Fase 3) ---------------------------------------
def _gestor_menu(conexion=Depends(obtener_conexion)) -> GestorMenu:
    """Arma el gestor del menú con la conexión de ESTA petición."""
    return GestorMenu(RepositorioProductosPostgres(conexion))


app.include_router(rutas_menu.router)
app.dependency_overrides[rutas_menu.obtener_gestor] = _gestor_menu