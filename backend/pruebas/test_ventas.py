"""
test_ventas.py — RN-10 (criterio 19): las ventas solo las ve el Administrador.

PAPEL EN LA ARQUITECTURA: demuestra que GestorVentas valida el rango y suma los
montos, y que la ruta exige el rol Administrador (RN-10). Usa dobles en memoria:
sin PostgreSQL.

Cómo correrlas:  pytest pruebas -k ventas -v
"""

from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.compartido.excepciones import ValidacionError
from app.main import app
from app.ventas_pagos import rutas_ventas
from app.ventas_pagos.repositorio import IRepositorioVentas
from app.ventas_pagos.servicio_ventas import GestorVentas


class RepoVentasFalso(IRepositorioVentas):
    def __init__(self, ventas=None):
        self.ventas = ventas or []

    def listar_ventas(self, desde, hasta):
        return list(self.ventas)


def _venta(id_pedido, monto):
    return {
        "id_pedido": id_pedido,
        "fecha": datetime(2026, 11, 14, 15, 30).isoformat(),
        "total": float(monto),
        "id_pago": id_pedido,
        "estado_pago": "Cobrado",
        "monto": float(monto),
        "fecha_pago": "2026-11-14",
    }


# --- GestorVentas (sin HTTP) --------------------------------------------------

def test_ventas_desde_posterior_a_hasta_da_validacion():
    gestor = GestorVentas(RepoVentasFalso())
    with pytest.raises(ValidacionError):
        gestor.consultar_ventas(date(2026, 12, 31), date(2026, 1, 1))


def test_ventas_sin_ventas_devuelve_total_cero():
    gestor = GestorVentas(RepoVentasFalso([]))
    resultado = gestor.consultar_ventas(date(2026, 1, 1), date(2026, 12, 31))
    assert resultado["cantidad"] == 0
    assert resultado["total_ventas"] == 0.0
    assert resultado["datos"] == []


def test_ventas_suma_los_montos_y_devuelve_los_datos():
    ventas = [_venta(1, Decimal("47600.00")), _venta(2, Decimal("23800.00"))]
    gestor = GestorVentas(RepoVentasFalso(ventas))
    resultado = gestor.consultar_ventas(date(2026, 1, 1), date(2026, 12, 31))
    assert resultado["cantidad"] == 2
    assert resultado["total_ventas"] == 71400.0
    assert len(resultado["datos"]) == 2


# --- Ruta (RN-10: solo Administrador) -----------------------------------------

@pytest.fixture
def http():
    original = app.dependency_overrides.get(rutas_ventas.obtener_gestor)
    app.dependency_overrides[rutas_ventas.obtener_gestor] = (
        lambda: GestorVentas(RepoVentasFalso([_venta(1, Decimal("47600.00"))]))
    )
    yield TestClient(app)
    if original is None:
        app.dependency_overrides.pop(rutas_ventas.obtener_gestor, None)
    else:
        app.dependency_overrides[rutas_ventas.obtener_gestor] = original


def _cabecera(rol: str) -> dict:
    return {"Authorization": f"Bearer {app.state.sesiones.crear(1, rol)}"}


def test_ventas_sin_sesion_da_401(http):
    assert http.get("/api/ventas-pagos?desde=2026-01-01&hasta=2026-12-31").status_code == 401


@pytest.mark.parametrize("rol", ["Mesero", "Chef", "Domiciliario", "Cliente"])
def test_ventas_otro_rol_da_403(http, rol):
    respuesta = http.get(
        "/api/ventas-pagos?desde=2026-01-01&hasta=2026-12-31",
        headers=_cabecera(rol),
    )
    assert respuesta.status_code == 403


def test_ventas_administrador_ve_la_lista_y_el_total(http):
    respuesta = http.get(
        "/api/ventas-pagos?desde=2026-01-01&hasta=2026-12-31",
        headers=_cabecera("Administrador"),
    )
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["cantidad"] == 1
    assert datos["total_ventas"] == 47600.0


def test_ventas_rango_invalido_da_422(http):
    respuesta = http.get(
        "/api/ventas-pagos?desde=2026-12-31&hasta=2026-01-01",
        headers=_cabecera("Administrador"),
    )
    assert respuesta.status_code == 422