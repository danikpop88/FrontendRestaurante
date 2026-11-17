"""
test_factory.py — Pruebas del patrón Factory Method de los pedidos (Fase 5).

PAPEL EN LA ARQUITECTURA: demuestra que cada creador construye SU tipo de pedido y
aplica sus reglas de creación: la mesa debe existir y RN-07 (domicilio sin teléfono
de contacto se rechaza). Los creadores no tienen SQL: reciben funciones, que aquí
son falsas. Sin PostgreSQL.

Cómo correrlas:  pytest pruebas -k factory -v     (y RN-07:  pytest pruebas -k telefono)
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.compartido.excepciones import ReglaNegocioError, ValidacionError
from app.compartido.reloj import RelojFalso
from app.pedidos.creadores.creador_pedidos import DatosPedido, ICreadorPedidos
from app.pedidos.creadores.creadores_concretos import CreadorPedidoDomicilio, CreadorPedidoMesa
from app.pedidos.modelos import DetallePedido, PedidoDomicilio, PedidoMesa, TipoPedido


@pytest.fixture
def reloj():
    return RelojFalso(datetime(2026, 11, 14, 15, 30))


@pytest.fixture
def detalle():
    return [DetallePedido(1, "Arepa", 2, Decimal("12000"))]


def _creador_mesa(reloj):
    return CreadorPedidoMesa(lambda numero: numero in (1, 2, 3), reloj)


def _creador_domicilio(reloj, telefono="3001112233"):
    return CreadorPedidoDomicilio(lambda id_cliente: telefono, reloj)


# --- CreadorPedidoMesa ------------------------------------------------------------

def test_factory_mesa_produce_un_pedido_de_mesa_en_recibido(reloj, detalle):
    pedido = _creador_mesa(reloj).crear_pedido(DatosPedido(detalle=detalle, numero_mesa=2))
    assert isinstance(pedido, PedidoMesa)
    assert pedido.obtener_tipo() == TipoPedido.EN_RESTAURANTE
    assert pedido.obtener_estado() == "Recibido"
    assert pedido.fecha == reloj.ahora()
    assert pedido.numero_mesa == 2


def test_factory_mesa_sin_numero_de_mesa_se_rechaza(reloj, detalle):
    with pytest.raises(ValidacionError):
        _creador_mesa(reloj).crear_pedido(DatosPedido(detalle=detalle))


def test_factory_mesa_inexistente_se_rechaza(reloj, detalle):
    with pytest.raises(ValidacionError):
        _creador_mesa(reloj).crear_pedido(DatosPedido(detalle=detalle, numero_mesa=99))


# --- CreadorPedidoDomicilio -------------------------------------------------------

def _datos_domicilio(detalle, **cambios):
    base = dict(detalle=detalle, id_cliente=7, direccion="Calle 10 # 20-30",
                metodo_pago="CONTRA_ENTREGA")
    base.update(cambios)
    return DatosPedido(**base)


def test_factory_domicilio_produce_un_pedido_a_domicilio(reloj, detalle):
    pedido = _creador_domicilio(reloj).crear_pedido(_datos_domicilio(detalle))
    assert isinstance(pedido, PedidoDomicilio)
    assert pedido.obtener_tipo() == TipoPedido.DOMICILIO
    assert pedido.direccion == "Calle 10 # 20-30"
    assert pedido.id_cliente == 7
    assert pedido.obtener_estado() == "Recibido"


def test_factory_rn07_con_telefono_se_acepta_el_pedido(reloj, detalle):
    pedido = _creador_domicilio(reloj, telefono="3001112233").crear_pedido(_datos_domicilio(detalle))
    assert pedido is not None


@pytest.mark.parametrize("telefono", [None, "", "   "])
def test_factory_rn07_telefono_sin_contacto_se_rechaza(reloj, detalle, telefono):
    with pytest.raises(ReglaNegocioError):
        _creador_domicilio(reloj, telefono=telefono).crear_pedido(_datos_domicilio(detalle))


def test_factory_domicilio_sin_direccion_ni_pago_devuelve_todos_los_motivos(reloj, detalle):
    datos = _datos_domicilio(detalle, direccion=None, metodo_pago=None)
    with pytest.raises(ValidacionError) as excepcion:
        _creador_domicilio(reloj).crear_pedido(datos)
    assert len(excepcion.value.errores) == 2


def test_factory_domicilio_solo_acepta_pago_contra_entrega(reloj, detalle):
    with pytest.raises(ValidacionError):
        _creador_domicilio(reloj).crear_pedido(_datos_domicilio(detalle, metodo_pago="TARJETA"))


def test_factory_los_creadores_son_icreador_pedidos(reloj):
    assert isinstance(_creador_mesa(reloj), ICreadorPedidos)
    assert isinstance(_creador_domicilio(reloj), ICreadorPedidos)