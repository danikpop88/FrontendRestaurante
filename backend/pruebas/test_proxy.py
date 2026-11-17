"""
test_proxy.py — Pruebas del patrón Proxy de pago (Fase 4).

PAPEL EN LA ARQUITECTURA: demuestra que ServicioPagoProxy valida el pedido y
registra la transacción ANTES de delegar, y que un pedido inválido no llega al
servicio real (Artículo 3). Usa repositorio y pedido falsos: sin PostgreSQL.

Cómo correrlas:  pytest pruebas -k proxy -v
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.compartido.excepciones import NoEncontradoError, ReglaNegocioError
from app.compartido.reloj import RelojFalso
from app.ventas_pagos.modelos import COBRADO, PENDIENTE_DE_COBRO
from app.ventas_pagos.repositorio import IRepositorioPagos
from app.ventas_pagos.servicio import IServicioPago, ServicioPagoProxy, ServicioPagoReal


class PedidoFalso:
    def __init__(self, id_pedido=1, valido=True, total=Decimal("47600.00"), id_cliente=7):
        self.id_pedido = id_pedido
        self.id_cliente = id_cliente
        self.total = total
        self._valido = valido

    def es_valido(self):
        return self._valido


class RepositorioPagosFalso(IRepositorioPagos):
    def __init__(self):
        self.pagos = {}
        self._siguiente = 1

    def guardar(self, pago):
        pago.id_pago = self._siguiente
        self._siguiente += 1
        self.pagos[pago.id_pedido] = pago
        return pago

    def obtener_por_pedido(self, id_pedido):
        return self.pagos.get(id_pedido)

    def actualizar(self, pago):
        self.pagos[pago.id_pedido] = pago


class RealEspia(IServicioPago):
    """Un servicio real falso que cuenta cuántas veces lo llaman."""

    def __init__(self):
        self.llamadas = []

    def registrar_pago(self, pedido):
        self.llamadas.append(("registrar_pago", pedido.id_pedido))

    def registrar_cobro(self, pedido):
        self.llamadas.append(("registrar_cobro", pedido.id_pedido))


@pytest.fixture
def reloj():
    return RelojFalso(datetime(2026, 11, 14, 15, 30))


@pytest.fixture
def repo():
    return RepositorioPagosFalso()


@pytest.fixture
def proxy(repo, reloj):
    return ServicioPagoProxy(ServicioPagoReal(repo, reloj), reloj)


# --- El pago nace pendiente y se cobra una sola vez ---------------------------

def test_proxy_pedido_valido_crea_pago_pendiente_de_cobro(proxy, repo):
    pago = proxy.registrar_pago(PedidoFalso())
    assert pago.id_pago is not None
    assert pago.estado_pago == PENDIENTE_DE_COBRO
    assert pago.monto == Decimal("47600.00")
    assert repo.obtener_por_pedido(1) is pago


def test_proxy_registrar_cobro_confirma_el_pago_con_la_fecha_del_reloj(proxy, repo, reloj):
    proxy.registrar_pago(PedidoFalso())
    reloj.adelantar(60 * 24)                      # al día siguiente
    pago = proxy.registrar_cobro(PedidoFalso())
    assert pago.estado_pago == COBRADO
    assert pago.fecha == date(2026, 11, 15)


def test_proxy_no_cobra_dos_veces(proxy):
    proxy.registrar_pago(PedidoFalso())
    proxy.registrar_cobro(PedidoFalso())
    with pytest.raises(ReglaNegocioError):
        proxy.registrar_cobro(PedidoFalso())


def test_proxy_cobrar_pedido_sin_pago_da_no_encontrado(proxy):
    with pytest.raises(NoEncontradoError):
        proxy.registrar_cobro(PedidoFalso(id_pedido=99))


# --- El proxy valida ANTES de delegar -----------------------------------------

def test_proxy_pedido_invalido_no_llega_al_servicio_real(reloj):
    real = RealEspia()
    proxy = ServicioPagoProxy(real, reloj)
    with pytest.raises(ReglaNegocioError):
        proxy.registrar_pago(PedidoFalso(valido=False))
    with pytest.raises(ReglaNegocioError):
        proxy.registrar_cobro(PedidoFalso(valido=False))
    assert real.llamadas == []
    assert proxy.transacciones == []


def test_proxy_pedido_valido_se_registra_y_luego_se_delega(reloj):
    real = RealEspia()
    proxy = ServicioPagoProxy(real, reloj)
    proxy.registrar_pago(PedidoFalso(id_pedido=5))
    assert real.llamadas == [("registrar_pago", 5)]
    assert proxy.transacciones == [(reloj.ahora(), "registrar_pago", 5)]


def test_proxy_es_un_iservicio_pago(proxy):
    assert isinstance(proxy, IServicioPago)