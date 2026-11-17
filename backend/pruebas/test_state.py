"""
test_state.py — Pruebas del patrón State del pedido (Fase 5).

PAPEL EN LA ARQUITECTURA: demuestra RN-01 (plazo de 5 minutos) y RN-04 (en cocina
no se cambia nada) dentro de los estados, con un RelojFalso: sin esperar y sin
PostgreSQL (Artículo 3). Cada regla tiene una prueba que se cumple y otra que se viola.

Cómo correrlas:  pytest pruebas -k state -v
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.compartido.excepciones import ReglaNegocioError, ValidacionError
from app.compartido.reloj import RelojFalso
from app.pedidos.estados.estados_concretos import (
    EstadoEnCamino,
    EstadoEnCocina,
    EstadoEntregado,
    EstadoRecibido,
    estado_desde_nombre,
)
from app.pedidos.modelos import DetallePedido, PedidoDomicilio, PedidoMesa, TipoPedido


@pytest.fixture
def reloj():
    return RelojFalso(datetime(2026, 11, 14, 15, 30))


@pytest.fixture
def pedido(reloj):
    return PedidoMesa(1, reloj.ahora(), 4, detalle=[DetallePedido(1, "Arepa", 2, Decimal("20000"))])


# --- RN-01: el plazo de 5 minutos ----------------------------------------------

def test_state_rn01_recibido_dentro_del_plazo_se_modifica_y_se_cancela(pedido, reloj):
    reloj.adelantar(4)
    pedido.modificar(reloj)                       # no lanza
    assert pedido.cancelar(reloj) is True


def test_state_rn01_recibido_con_cinco_minutos_se_rechaza(pedido, reloj):
    reloj.adelantar(5)
    with pytest.raises(ReglaNegocioError):
        pedido.modificar(reloj)
    with pytest.raises(ReglaNegocioError):
        pedido.cancelar(reloj)


# --- RN-04: en cocina no se modifica ni se cancela ------------------------------

def test_state_rn04_en_cocina_rechaza_modificar_y_cancelar(pedido, reloj):
    pedido.siguiente()                            # el chef lo toma
    assert pedido.obtener_estado() == "EnCocina"
    with pytest.raises(ReglaNegocioError):
        pedido.modificar(reloj)
    with pytest.raises(ReglaNegocioError):
        pedido.cancelar(reloj)


def test_state_rn04_en_cocina_rechaza_aunque_el_plazo_no_haya_vencido(pedido, reloj):
    pedido.siguiente()
    reloj.adelantar(1)                            # solo 1 minuto: igual se rechaza
    with pytest.raises(ReglaNegocioError):
        pedido.cancelar(reloj)


def test_state_en_camino_y_entregado_tampoco_se_cambian(reloj):
    pedido = PedidoMesa(1, reloj.ahora(), 4, estado=EstadoEnCamino())
    with pytest.raises(ReglaNegocioError):
        pedido.cancelar(reloj)
    entregado = PedidoMesa(2, reloj.ahora(), 4, estado=EstadoEntregado())
    with pytest.raises(ReglaNegocioError):
        entregado.modificar(reloj)


# --- Transiciones ---------------------------------------------------------------

def test_state_transiciones_validas_hasta_entregado(pedido):
    nombres = [pedido.obtener_estado()]
    for _ in range(3):
        pedido.siguiente()
        nombres.append(pedido.obtener_estado())
    assert nombres == ["Recibido", "EnCocina", "EnCamino", "Entregado"]


def test_state_entregado_no_tiene_siguiente(pedido):
    for _ in range(3):
        pedido.siguiente()
    with pytest.raises(ReglaNegocioError):
        pedido.siguiente()


def test_state_el_pedido_nace_en_recibido(pedido):
    assert pedido.obtener_estado() == "Recibido"
    assert isinstance(pedido._estado, EstadoRecibido)


def test_state_estado_desde_nombre_reconstruye_cada_estado():
    assert isinstance(estado_desde_nombre("EnCocina"), EstadoEnCocina)
    assert estado_desde_nombre("Entregado").obtener_estado() == "Entregado"
    with pytest.raises(ValueError):
        estado_desde_nombre("Listo")              # "Listo" no es un estado (D20)


# --- Dominio del pedido ----------------------------------------------------------

def test_state_total_incluye_el_iva_del_19_por_ciento(pedido):
    assert pedido.total == Decimal("47600.00")    # 2 x 20000 x 1,19


def test_state_producto_repetido_suma_las_cantidades(pedido):
    pedido.agregar_producto(DetallePedido(1, "Arepa", 3, Decimal("20000")))
    assert len(pedido.detalle) == 1 and pedido.detalle[0].cantidad == 5


def test_state_cantidad_menor_que_uno_se_rechaza(pedido):
    with pytest.raises(ValidacionError):
        pedido.agregar_producto(DetallePedido(2, "Flan", 0, Decimal("5000")))


def test_state_eliminar_y_reemplazar_detalle(pedido):
    pedido.eliminar_producto(1)
    assert pedido.detalle == [] and pedido.es_valido() is False
    pedido.reemplazar_detalle([DetallePedido(7, "Flan", 1, Decimal("5000"))])
    assert pedido.es_valido() is True


def test_state_es_valido_del_domicilio_pide_direccion(reloj):
    detalle = [DetallePedido(1, "Arepa", 1, Decimal("12000"))]
    assert PedidoDomicilio(None, reloj.ahora(), 7, "Calle 1", detalle=detalle).es_valido()
    assert not PedidoDomicilio(None, reloj.ahora(), 7, "  ", detalle=detalle).es_valido()


def test_state_tipo_de_cada_pedido(pedido, reloj):
    assert pedido.obtener_tipo() == TipoPedido.EN_RESTAURANTE
    assert PedidoDomicilio(None, reloj.ahora(), 7, "Calle 1").obtener_tipo() == TipoPedido.DOMICILIO


def test_state_observadores_reciben_el_aviso(pedido):
    class Observador:
        def __init__(self):
            self.recibidos = []

        def actualizar(self, p):
            self.recibidos.append(p)

    uno, dos = Observador(), Observador()
    pedido.agregar_observador(uno)
    pedido.agregar_observador(dos)
    pedido.quitar_observador(dos)
    pedido.notificar_observadores()
    assert uno.recibidos == [pedido] and dos.recibidos == []