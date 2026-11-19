"""
test_reservas.py — Criterio 20: el administrador consulta las reservas vigentes.

PAPEL EN LA ARQUITECTURA: demuestra que Reserva.es_vigente() filtra por fecha,
que GestorReservas lo aplica y que la ruta solo la ve el Administrador
(Contratos §8). Usa dobles en memoria: sin PostgreSQL.

Cómo correrlas:  pytest pruebas -k reservas -v
"""

from datetime import date, time, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.reservas import rutas as rutas_reservas
from app.reservas.modelos import Mesa, Reserva
from app.reservas.repositorio import IRepositorioReservas
from app.reservas.servicio import GestorReservas


def _mesa(numero=5):
    return Mesa(id_mesa=numero, numero_mesa=numero, capacidad_personas=4, disponibilidad=True)


def _reserva(id_reserva, fecha, mesa_numero=5, cliente=None):
    return Reserva(
        id_reserva=id_reserva,
        mesa=_mesa(mesa_numero),
        nombre_titular=f"Titular {id_reserva}",
        telefono_titular="3109876543",
        fecha_reserva=fecha,
        hora_reserva=time(19, 30),
        id_cliente=cliente,
    )


class RepoReservasFalso(IRepositorioReservas):
    def __init__(self, reservas=None):
        self.reservas = reservas or []

    def listar_vigentes(self):
        return list(self.reservas)


# --- Reserva.es_vigente() ------------------------------------------------------

def test_reserva_pasada_no_es_vigente():
    assert _reserva(1, date.today() - timedelta(days=1)).es_vigente() is False


def test_reserva_de_hoy_es_vigente():
    assert _reserva(2, date.today()).es_vigente() is True


def test_reserva_futura_es_vigente():
    assert _reserva(3, date.today() + timedelta(days=5)).es_vigente() is True


# --- GestorReservas.listar_vigentes() ----------------------------------------

def test_reservas_gestor_filtra_las_no_vigentes():
    reservas = [
        _reserva(1, date.today() - timedelta(days=3)),   # vencida
        _reserva(2, date.today()),                       # hoy
        _reserva(3, date.today() + timedelta(days=7)),   # futura
    ]
    gestor = GestorReservas(RepoReservasFalso(reservas))
    vigentes = gestor.listar_vigentes()
    assert [r.id_reserva for r in vigentes] == [2, 3]


def test_reservas_gestor_sin_reservas_devuelve_lista_vacia():
    assert GestorReservas(RepoReservasFalso()).listar_vigentes() == []


# --- Ruta (solo Administrador, Contratos §8) ---------------------------------

@pytest.fixture
def http():
    reservas = [
        _reserva(1, date.today() + timedelta(days=5), mesa_numero=5),
        _reserva(2, date.today() + timedelta(days=7), mesa_numero=3),
    ]
    original = app.dependency_overrides.get(rutas_reservas.obtener_gestor)
    app.dependency_overrides[rutas_reservas.obtener_gestor] = (
        lambda: GestorReservas(RepoReservasFalso(reservas))
    )
    yield TestClient(app)
    if original is None:
        app.dependency_overrides.pop(rutas_reservas.obtener_gestor, None)
    else:
        app.dependency_overrides[rutas_reservas.obtener_gestor] = original


def _cabecera(rol: str) -> dict:
    return {"Authorization": f"Bearer {app.state.sesiones.crear(1, rol)}"}


def test_reservas_sin_sesion_da_401(http):
    assert http.get("/api/reservas").status_code == 401


@pytest.mark.parametrize("rol", ["Mesero", "Chef", "Domiciliario", "Cliente"])
def test_reservas_otro_rol_da_403(http, rol):
    assert http.get("/api/reservas", headers=_cabecera(rol)).status_code == 403


def test_reservas_administrador_ve_las_reservas_con_mesa(http):
    respuesta = http.get("/api/reservas", headers=_cabecera("Administrador"))
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["total"] == 2
    primera = datos["datos"][0]
    assert primera["nombre_titular"] == "Titular 1"
    assert primera["numero_mesa"] == 5
    assert primera["hora_reserva"] == "19:30:00"
    assert primera["fecha_reserva"] == (date.today() + timedelta(days=5)).isoformat()