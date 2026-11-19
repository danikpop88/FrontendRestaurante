"""
test_reasignacion.py — RN-08 (criterio 16): un pedido "EnCamino" no se reasigna.

PAPEL EN LA ARQUITECTURA: el criterio 16 dice que un pedido "En camino" no se
reasigna. Lo cumple Domicilio.asignarDomiciliario() y lo propaga
GestorDomicilios convirtiendo el ValueError en ReglaNegocioError (409).
Usa dobles en memoria: sin PostgreSQL.

Cómo correrlas:  pytest pruebas -k reasignacion -v
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.compartido.excepciones import ReglaNegocioError
from app.compartido.reloj import RelojFalso
from app.domicilios.modelos import Domicilio
from app.domicilios.repositorio import IRepositorioDomicilios
from app.domicilios.servicio import GestorDomicilios
from app.pedidos.modelos import DetallePedido, PedidoDomicilio
from app.ventas_pagos.servicio import IServicioPago


class PagoFalso(IServicioPago):
    def registrar_pago(self, pedido):
        raise NotImplementedError

    def registrar_cobro(self, pedido):
        raise NotImplementedError


class RepoDomiciliosFalso(IRepositorioDomicilios):
    def __init__(self, id_domiciliario_libre=5, domicilio_por_pedido=None):
        self.id_domiciliario_libre = id_domiciliario_libre
        self.domicilio_por_pedido = domicilio_por_pedido
        self.actualizados: list[Domicilio] = []

    def obtener_menos_pedidos_activos(self):
        return self.id_domiciliario_libre

    def crear(self, domicilio):
        return domicilio

    def obtener_por_id(self, id_domicilio):
        return None

    def listar_por_domiciliario(self, id_domiciliario):
        return []

    def actualizar(self, domicilio):
        self.actualizados.append(domicilio)

    def obtener_por_pedido(self, id_pedido):
        return self.domicilio_por_pedido


@pytest.fixture
def reloj():
    return RelojFalso(datetime(2026, 11, 14, 15, 30))


@pytest.fixture
def pedido_en_camino(reloj):
    p = PedidoDomicilio(1, reloj.ahora(), 7, "Calle 1",
                        detalle=[DetallePedido(1, "Arepa", 1, Decimal("12000"))])
    p.siguiente()   # EnCocina
    p.siguiente()   # EnCamino
    return p


@pytest.fixture
def pedido_recibido(reloj):
    return PedidoDomicilio(2, reloj.ahora(), 7, "Calle 1",
                           detalle=[DetallePedido(1, "Arepa", 1, Decimal("12000"))])


# --- Domicilio.asignarDomiciliario (la regla, en el dominio) ------------------

def test_rn08_en_camino_con_domiciliario_no_se_reasigna(pedido_en_camino):
    domicilio = Domicilio(1, pedido_en_camino, id_domiciliario=3, direccion="Calle 1")
    with pytest.raises(ValueError):
        domicilio.asignarDomiciliario(5)


def test_rn08_en_camino_sin_domiciliario_si_se_asigna(pedido_en_camino):
    domicilio = Domicilio(1, pedido_en_camino, id_domiciliario=None, direccion="Calle 1")
    domicilio.asignarDomiciliario(5)
    assert domicilio.id_domiciliario == 5


def test_rn08_recibido_se_puede_asignar_aunque_ya_tenga_uno(pedido_recibido):
    domicilio = Domicilio(2, pedido_recibido, id_domiciliario=3, direccion="Calle 1")
    domicilio.asignarDomiciliario(5)
    assert domicilio.id_domiciliario == 5


# --- GestorDomicilios.asignar_automaticamente (la regla, en el servicio) ------

def test_rn08_gestor_rechaza_reasignacion_de_en_camino(pedido_en_camino):
    domicilio = Domicilio(1, pedido_en_camino, id_domiciliario=3, direccion="Calle 1")
    repo = RepoDomiciliosFalso(id_domiciliario_libre=5)
    gestor = GestorDomicilios(repo, PagoFalso())
    with pytest.raises(ReglaNegocioError):
        gestor.asignar_automaticamente(domicilio)


def test_rn08_gestor_asigna_al_domiciliario_con_menos_pedidos(pedido_recibido):
    domicilio = Domicilio(2, pedido_recibido, id_domiciliario=None, direccion="Calle 1")
    repo = RepoDomiciliosFalso(id_domiciliario_libre=5)
    gestor = GestorDomicilios(repo, PagoFalso())
    gestor.asignar_automaticamente(domicilio)
    assert domicilio.id_domiciliario == 5
    assert repo.actualizados == [domicilio]


def test_rn08_gestor_sin_domiciliarios_disponibles_deja_pendiente(pedido_recibido):
    domicilio = Domicilio(2, pedido_recibido, id_domiciliario=None, direccion="Calle 1")
    repo = RepoDomiciliosFalso(id_domiciliario_libre=None)
    gestor = GestorDomicilios(repo, PagoFalso())
    gestor.asignar_automaticamente(domicilio)
    assert domicilio.id_domiciliario is None
    assert repo.actualizados == []