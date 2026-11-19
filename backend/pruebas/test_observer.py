"""
test_observer.py — Pruebas del patrón Observer (Fase 7).

PAPEL EN LA ARQUITECTURA: demuestra que, al marcar listo un pedido, el pedido
notifica SOLO al actor que corresponde: Mesero en un pedido de mesa,
Domiciliario en uno a domicilio. Usa dobles en memoria: sin PostgreSQL.

Cómo correrlas:  pytest pruebas -k observer -v
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.cocina.repositorio import IRepositorioCocina
from app.cocina.servicio import GestorCocina
from app.compartido.reloj import RelojFalso
from app.notificaciones.modelos import DomiciliarioObservador, MeseroObservador
from app.pedidos.modelos import DetallePedido, PedidoDomicilio, PedidoMesa, TipoPedido
from app.pedidos.repositorio import IRepositorioPedidos


class PushEspia:
    """Servicio de push falso: solo guarda lo que le piden enviar."""

    def __init__(self):
        self.enviados: list[tuple[int, str]] = []

    def enviar_aviso(self, id_usuario: int, mensaje: str) -> None:
        self.enviados.append((id_usuario, mensaje))


class RepoPedidosFalso(IRepositorioPedidos):
    def __init__(self, pedidos: dict | None = None):
        self._pedidos = pedidos or {}

    def crear(self, pedido):
        self._pedidos[pedido.id_pedido] = pedido
        return pedido

    def obtener_por_id(self, id_pedido):
        return self._pedidos.get(id_pedido)

    def listar_de_cliente(self, id_cliente, estado_pedido=None):
        return []

    def listar_de_mesa(self, estado_pedido=None):
        return []

    def actualizar(self, pedido):
        self._pedidos[pedido.id_pedido] = pedido

    def eliminar(self, id_pedido):
        self._pedidos.pop(id_pedido, None)

    def obtener_telefono_cliente(self, id_cliente):
        return "3001112233"

    def existe_mesa(self, numero_mesa):
        return True


class RecoCocinaFalso(IRepositorioCocina):
    def listar_cola(self, tipo_pedido=None):
        return []


class GestorDomiciliosFalso:
    """Solo devuelve un domicilio con id_domiciliario para que el observer avise."""

    def __init__(self, id_domiciliario=5):
        self.id_domiciliario = id_domiciliario
        self.llamado_con: list[int] = []

    def asignar_automaticamente_por_pedido(self, id_pedido: int):
        self.llamado_con.append(id_pedido)
        return type("D", (), {"id_domiciliario": self.id_domiciliario})()


@pytest.fixture
def reloj():
    return RelojFalso(datetime(2026, 11, 14, 15, 30))


@pytest.fixture
def push():
    return PushEspia()


@pytest.fixture
def detalle():
    return [DetallePedido(1, "Arepa", 1, Decimal("12000"))]


# --- Observadores concretos ---------------------------------------------------

def test_observer_mesero_envia_aviso_con_numero_de_mesa(push, detalle, reloj):
    pedido = PedidoMesa(1, reloj.ahora(), 4, detalle=detalle)
    pedido.id_mesero = 3
    MeseroObservador(push).actualizar(pedido)
    assert push.enviados == [(3, "El pedido de la mesa 4 está listo.")]


def test_observer_domiciliario_envia_aviso_si_hay_domiciliario(push, detalle, reloj):
    pedido = PedidoDomicilio(2, reloj.ahora(), 7, "Calle 1", detalle=detalle)
    pedido.id_domiciliario = 9
    DomiciliarioObservador(push).actualizar(pedido)
    assert push.enviados == [
        (9, "Tienes un nuevo pedido a domicilio listo para entregar (Pedido #2).")
    ]


def test_observer_domiciliario_no_avisa_si_no_hay_domiciliario(push, detalle, reloj):
    pedido = PedidoDomicilio(3, reloj.ahora(), 7, "Calle 1", detalle=detalle)
    DomiciliarioObservador(push).actualizar(pedido)
    assert push.enviados == []


# --- GestorCocina notifica al actor correcto ----------------------------------

def _en_cocina(pedido):
    pedido.siguiente()   # Recibido -> EnCocina
    return pedido


def _gestor(reloj, push, gestor_dom, pedidos):
    return GestorCocina(
        RecoCocinaFalso(),
        RepoPedidosFalso(pedidos),
        reloj,
        MeseroObservador(push),
        DomiciliarioObservador(push),
        gestor_dom,
    )


def test_observer_marcar_listo_de_mesa_avisa_al_mesero_y_no_al_domiciliario(
    push, detalle, reloj
):
    pedido = _en_cocina(PedidoMesa(1, reloj.ahora(), 4, detalle=detalle))
    pedido.id_mesero = 3
    gestor = _gestor(reloj, push, GestorDomiciliosFalso(), {1: pedido})

    gestor.marcar_listo(1, id_chef=2)

    assert push.enviados == [(3, "El pedido de la mesa 4 está listo.")]


def test_observer_marcar_listo_de_domicilio_asigna_y_avisa_al_domiciliario(
    push, detalle, reloj
):
    pedido = _en_cocina(PedidoDomicilio(2, reloj.ahora(), 7, "Calle 1", detalle=detalle))
    dom = GestorDomiciliosFalso(id_domiciliario=9)
    gestor = _gestor(reloj, push, dom, {2: pedido})

    gestor.marcar_listo(2, id_chef=2)

    assert dom.llamado_con == [2]
    assert push.enviados == [
        (9, "Tienes un nuevo pedido a domicilio listo para entregar (Pedido #2).")
    ]


def test_observer_marcar_listo_sin_domiciliarios_no_avisa(push, detalle, reloj):
    pedido = _en_cocina(PedidoDomicilio(4, reloj.ahora(), 7, "Calle 1", detalle=detalle))
    dom = GestorDomiciliosFalso(id_domiciliario=None)
    gestor = _gestor(reloj, push, dom, {4: pedido})

    gestor.marcar_listo(4, id_chef=2)
    assert push.enviados == []