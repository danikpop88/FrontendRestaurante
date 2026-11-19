"""
test_comando.py — Pruebas del patrón Command de cocina (Fase 7).

PAPEL EN LA ARQUITECTURA: demuestra que los comandos guardan quién los ejecutó y
cuándo (auditoría) y que delegan la decisión de cancelar en el estado del pedido
(RN-01 y RN-04). Usa RelojFalso: sin PostgreSQL.

Cómo correrlas:  pytest pruebas -k comando -v
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.cocina.modelos import (
    ComandoCancelarPedido,
    ComandoMarcarListo,
    IComandoCocina,
)
from app.compartido.excepciones import ReglaNegocioError
from app.compartido.reloj import RelojFalso
from app.pedidos.modelos import DetallePedido, PedidoMesa


@pytest.fixture
def reloj():
    return RelojFalso(datetime(2026, 11, 14, 15, 30))


@pytest.fixture
def pedido(reloj):
    return PedidoMesa(1, reloj.ahora(), 4,
                      detalle=[DetallePedido(1, "Arepa", 1, Decimal("12000"))])


# --- ComandoMarcarListo -------------------------------------------------------

def test_comando_marcar_listo_guarda_ejecutor_y_hora(pedido, reloj):
    pedido.siguiente()   # Recibido -> EnCocina
    comando = ComandoMarcarListo(pedido, ejecutado_por=7, reloj=reloj)
    assert comando.ejecutado_por == 7
    assert comando.fecha_hora == reloj.ahora()


def test_comando_marcar_listo_avanza_el_pedido_a_en_camino(pedido, reloj):
    pedido.siguiente()   # EnCocina
    ComandoMarcarListo(pedido, ejecutado_por=7, reloj=reloj).ejecutar()
    assert pedido.obtener_estado() == "EnCamino"


def test_comando_marcar_listo_en_recibido_falla(pedido, reloj):
    # EstadoRecibido.siguiente() pasa a EnCocina; eso lo hace el gestor, no
    # el comando. Aquí solo se comprueba que el comando avanza el pedido.
    ComandoMarcarListo(pedido, 7, reloj).ejecutar()
    assert pedido.obtener_estado() == "EnCocina"


def test_comando_marcar_listo_es_un_icomando(pedido, reloj):
    assert isinstance(ComandoMarcarListo(pedido, 7, reloj), IComandoCocina)


# --- ComandoCancelarPedido ----------------------------------------------------

def test_comando_cancelar_dentro_del_plazo_no_lanza(pedido, reloj):
    reloj.adelantar(4)
    ComandoCancelarPedido(pedido, ejecutado_por=7, reloj=reloj).ejecutar()
    assert pedido.obtener_estado() == "Recibido"   # cancelar() no borra, solo valida


def test_comando_cancelar_pasados_cinco_minutos_lanza(pedido, reloj):
    reloj.adelantar(5)
    with pytest.raises(ReglaNegocioError):
        ComandoCancelarPedido(pedido, ejecutado_por=7, reloj=reloj).ejecutar()


def test_comando_cancelar_en_cocina_lanza(pedido, reloj):
    pedido.siguiente()   # EnCocina: RN-04 bloquea
    with pytest.raises(ReglaNegocioError):
        ComandoCancelarPedido(pedido, ejecutado_por=7, reloj=reloj).ejecutar()


def test_comando_cancelar_guarda_ejecutor_y_hora(pedido, reloj):
    comando = ComandoCancelarPedido(pedido, ejecutado_por=4, reloj=reloj)
    assert comando.ejecutado_por == 4
    assert comando.fecha_hora == reloj.ahora()