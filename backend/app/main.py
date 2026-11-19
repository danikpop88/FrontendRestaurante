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
from app.compartido.reloj import RelojSistema
from app.compartido.seguridad import GestorSesiones
from app.menu import rutas as rutas_menu
from app.menu.repositorio_postgres import RepositorioProductosPostgres
from app.menu.servicio import GestorMenu
from app.pedidos import rutas as rutas_pedidos
from app.pedidos.creadores.creadores_concretos import (
    CreadorPedidoDomicilio,
    CreadorPedidoMesa,
)
from app.pedidos.modelos import TipoPedido
from app.pedidos.repositorio_postgres import RepositorioPedidosPostgres
from app.pedidos.servicio import GestorPedidos
from app.ventas_pagos.servicio import ServicioPagoProxy, ServicioPagoReal

# --- Importaciones de la FASE 6 (Domicilios) ---
from app.domicilios import rutas as rutas_domicilios
from app.domicilios.repositorio_postgres import RepositorioDomiciliosPostgres
from app.domicilios.servicio import GestorDomicilios

# --- FASE 7 ---
from app.cocina import rutas as rutas_cocina
from app.cocina.repositorio_postgres import RepositorioCocinaPostgres
from app.cocina.servicio import GestorCocina
from app.notificaciones import rutas as rutas_notificaciones
from app.notificaciones.repositorio_postgres import RepositorioAvisosPostgres
from app.integraciones.servicio_push import ServicioPush
from app.notificaciones.modelos import MeseroObservador, DomiciliarioObservador
from app.cocina.modelos import Chef
from app.notificaciones.servicio import GestorNotificaciones

# --- FASE 8 (Ventas y Reservas) ---
from app.ventas_pagos import rutas_ventas
from app.reservas import rutas as rutas_reservas
from app.reservas.repositorio_postgres import RepositorioReservasPostgres
from app.reservas.servicio import GestorReservas
from app.ventas_pagos.repositorio_postgres import (
    RepositorioPagosPostgres,
    RepositorioVentasPostgres,
)
from app.ventas_pagos.servicio_ventas import GestorVentas

registro = logging.getLogger("mesa_abuela")

app = FastAPI(title="La mesa de la abuela")

# --- Ensamblaje de las dependencias concretas -------------------------------
reloj = RelojSistema()
app.state.sesiones = GestorSesiones(reloj)

CLASES_EMPLEADO = {
    "Mesero": Mesero,
    "Domiciliario": Domiciliario,
    "Administrador": Administrador,
    "Chef": Chef,
}

# --- CORS: solo el origen del front puede llamar a la API (Artículo 11) -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.ORIGEN_FRONT],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# --- Traducción de errores a HTTP (Plan §5.10) -------------------------------
def _respuesta_error(
    estado: int, mensaje: str, errores: list[str] | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=estado,
        content={"estado": estado, "mensaje": mensaje, "errores": errores or []},
    )


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
async def manejar_validacion(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    errores = []
    for detalle in error.errors():
        campo = str(detalle["loc"][-1]) if detalle["loc"] else "datos"
        if detalle["type"] == "missing":
            errores.append(f"El campo '{campo}' es obligatorio.")
        elif detalle["type"] == "value_error":
            errores.append(str(detalle["msg"]).removeprefix("Value error, "))
        else:
            errores.append(f"El campo '{campo}' no es válido.")
    return _respuesta_error(422, "Los datos enviados no son válidos.", errores)


@app.exception_handler(ValidacionError)
async def manejar_validacion_negocio(
    request: Request, error: ValidacionError
) -> JSONResponse:
    return _respuesta_error(422, str(error), error.errores)


@app.exception_handler(Exception)
async def manejar_error_inesperado(request: Request, error: Exception) -> JSONResponse:
    registro.exception("Error inesperado en %s", request.url.path)
    return _respuesta_error(
        500, "Ocurrió un error inesperado. Intente de nuevo más tarde."
    )


# --- Módulo: Autenticación de usuarios (Fase 2) -----------------------------
def _gestor_autenticacion(conexion=Depends(obtener_conexion)) -> GestorAutenticacion:
    repositorio = RepositorioUsuariosPostgres(conexion, CLASES_EMPLEADO)
    return GestorAutenticacion(repositorio, app.state.sesiones, CLASES_EMPLEADO)


app.include_router(rutas_autenticacion.router)
app.dependency_overrides[rutas_autenticacion.obtener_gestor] = _gestor_autenticacion


# --- Módulo: Menú y productos (Fase 3) ---------------------------------------
def _gestor_menu(conexion=Depends(obtener_conexion)) -> GestorMenu:
    return GestorMenu(RepositorioProductosPostgres(conexion))


app.include_router(rutas_menu.router)
app.dependency_overrides[rutas_menu.obtener_gestor] = _gestor_menu


# --- Módulo: Pedidos (Fase 5) ------------------------------------------------
def _gestor_pedidos(conexion=Depends(obtener_conexion)) -> GestorPedidos:
    repositorio = RepositorioPedidosPostgres(conexion)
    creadores = {
        TipoPedido.EN_RESTAURANTE: CreadorPedidoMesa(repositorio.existe_mesa, reloj),
        TipoPedido.DOMICILIO: CreadorPedidoDomicilio(
            repositorio.obtener_telefono_cliente, reloj
        ),
    }
    servicio_pago = ServicioPagoProxy(
        ServicioPagoReal(RepositorioPagosPostgres(conexion), reloj),
        reloj,
    )
    return GestorPedidos(
        repositorio,
        RepositorioProductosPostgres(conexion),
        creadores,
        servicio_pago,
        reloj,
    )


app.include_router(rutas_pedidos.router)
app.dependency_overrides[rutas_pedidos.obtener_gestor] = _gestor_pedidos


# --- Módulo: Domicilios (Fase 6) ---------------------------------------------
def _gestor_domicilios(conexion=Depends(obtener_conexion)) -> GestorDomicilios:
    """Arma el gestor de domicilios con su repositorio y el Proxy de pago."""
    repositorio = RepositorioDomiciliosPostgres(conexion)

    # Reutilizamos el Proxy de pago que ya se usa en pedidos para registrar el cobro
    servicio_pago = ServicioPagoProxy(
        ServicioPagoReal(RepositorioPagosPostgres(conexion), reloj), reloj
    )

    return GestorDomicilios(repositorio, servicio_pago)


app.include_router(rutas_domicilios.router)
app.dependency_overrides[rutas_domicilios.obtener_gestor] = _gestor_domicilios


# --- Ensamblaje Fase 7: Cocina y Notificaciones ---
def _gestor_cocina(conexion=Depends(obtener_conexion)) -> GestorCocina:
    servicio_push = ServicioPush(conexion)
    obs_mesero = MeseroObservador(servicio_push)
    obs_domiciliario = DomiciliarioObservador(servicio_push)

    # Instanciamos GestorDomicilios para pasárselo a Cocina (Fase 6)
    servicio_pago = ServicioPagoProxy(
        ServicioPagoReal(RepositorioPagosPostgres(conexion), reloj), reloj
    )
    gestor_dom = GestorDomicilios(
        RepositorioDomiciliosPostgres(conexion), servicio_pago
    )

    return GestorCocina(
        RepositorioCocinaPostgres(conexion),
        RepositorioPedidosPostgres(conexion),
        reloj,
        obs_mesero,
        obs_domiciliario,
        gestor_dom,
    )


app.include_router(rutas_cocina.router)
app.dependency_overrides[rutas_cocina.obtener_gestor] = _gestor_cocina


def _gestor_notificaciones(conexion=Depends(obtener_conexion)) -> GestorNotificaciones:
    return GestorNotificaciones(RepositorioAvisosPostgres(conexion))


app.include_router(rutas_notificaciones.router)
app.dependency_overrides[rutas_notificaciones.obtener_gestor] = _gestor_notificaciones


# --- Ensamblaje Fase 8: Ventas y Reservas ---
def _gestor_ventas(conexion=Depends(obtener_conexion)) -> GestorVentas:
    return GestorVentas(RepositorioVentasPostgres(conexion))


def _gestor_reservas(conexion=Depends(obtener_conexion)) -> GestorReservas:
    return GestorReservas(RepositorioReservasPostgres(conexion))


app.include_router(rutas_ventas.router)
app.dependency_overrides[rutas_ventas.obtener_gestor] = _gestor_ventas

app.include_router(rutas_reservas.router)
app.dependency_overrides[rutas_reservas.obtener_gestor] = _gestor_reservas