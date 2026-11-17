"""
test_pedidos.py — Pruebas del GestorPedidos y de las rutas de pedidos (Fase 5).

PAPEL EN LA ARQUITECTURA: demuestra las reglas del gestor (RN-05, permisos por rol,
carrito, RN-01 y RN-04 al modificar y cancelar) y que las rutas las traducen a su
código HTTP. Usa repositorios FALSOS en memoria y un RelojFalso: sin PostgreSQL.
Los nombres llevan "reglas" (gestor) y "rutas" para filtrarlos con -k.

Cómo correrlas:  pytest pruebas -k pedidos -v
"""

from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.compartido.excepciones import (
    NoEncontradoError,
    ReglaNegocioError,
    SinPermisoError,
    ValidacionError,
)
from app.compartido.reloj import RelojFalso
from app.main import app
from app.menu.modelos import Producto
from app.menu.repositorio import IRepositorioProductos
from app.pedidos import rutas as rutas_pedidos
from app.pedidos.creadores.creadores_concretos import CreadorPedidoDomicilio, CreadorPedidoMesa
from app.pedidos.modelos import PedidoDomicilio, TipoPedido
from app.pedidos.repositorio import IRepositorioPedidos
from app.pedidos.servicio import GestorPedidos, ItemPedido
from app.ventas_pagos.servicio import IServicioPago


class RepositorioProductosFalso(IRepositorioProductos):
    def __init__(self):
        self.productos = {
            1: Producto(1, "Arepa paisa rellena", None, Decimal("12000.00"), "Entradas", True),
            2: Producto(2, "Picada de la abuela", None, Decimal("38000.00"), "Platos Fuertes", False),
        }

    def listar(self, categoria=None):
        return list(self.productos.values())

    def obtener_por_id(self, id_producto):
        return self.productos.get(id_producto)

    def listar_categorias(self):
        return sorted({p.categoria for p in self.productos.values()})

    def crear(self, producto):
        raise NotImplementedError

    def actualizar(self, producto):
        raise NotImplementedError


class RepositorioPedidosFalso(IRepositorioPedidos):
    TELEFONOS = {7: "3001112233", 8: None}      # el cliente 8 no tiene teléfono
    MESAS = {1, 2, 3, 4}

    def __init__(self):
        self.pedidos = {}
        self._siguiente = 1

    def crear(self, pedido):
        pedido.id_pedido = self._siguiente
        self._siguiente += 1
        self.pedidos[pedido.id_pedido] = pedido
        return pedido

    def obtener_por_id(self, id_pedido):
        return self.pedidos.get(id_pedido)

    def listar_de_cliente(self, id_cliente, estado_pedido=None):
        return [p for p in self.pedidos.values() if p.id_cliente == id_cliente
                and (estado_pedido is None or p.obtener_estado() == estado_pedido)]

    def listar_de_mesa(self, estado_pedido=None):
        return [p for p in self.pedidos.values() if p.obtener_tipo() == TipoPedido.EN_RESTAURANTE
                and (estado_pedido is None or p.obtener_estado() == estado_pedido)]

    def actualizar(self, pedido):
        self.pedidos[pedido.id_pedido] = pedido

    def eliminar(self, id_pedido):
        self.pedidos.pop(id_pedido, None)

    def obtener_telefono_cliente(self, id_cliente):
        return self.TELEFONOS.get(id_cliente)

    def existe_mesa(self, numero_mesa):
        return numero_mesa in self.MESAS


class PagoFalso(IServicioPago):
    def registrar_pago(self, pedido):
        raise NotImplementedError

    def registrar_cobro(self, pedido):
        raise NotImplementedError


@pytest.fixture
def reloj():
    return RelojFalso(datetime(2026, 11, 14, 15, 30))


@pytest.fixture
def repo():
    return RepositorioPedidosFalso()


@pytest.fixture
def gestor(repo, reloj):
    creadores = {
        TipoPedido.EN_RESTAURANTE: CreadorPedidoMesa(repo.existe_mesa, reloj),
        TipoPedido.DOMICILIO: CreadorPedidoDomicilio(repo.obtener_telefono_cliente, reloj),
    }
    return GestorPedidos(repo, RepositorioProductosFalso(), creadores, PagoFalso(), reloj)


def _domicilio(gestor, id_cliente=7, cantidad=2):
    return gestor.crear_pedido("Cliente", id_cliente, TipoPedido.DOMICILIO,
                               [ItemPedido(1, cantidad)], "Calle 1 # 2-3", "CONTRA_ENTREGA")


def _orden_mesa(gestor, mesa=2):
    return gestor.crear_pedido("Mesero", 3, TipoPedido.EN_RESTAURANTE,
                               [ItemPedido(1, 1)], numero_mesa=mesa)


# =====================================================================
# Reglas del GestorPedidos
# =====================================================================

def test_reglas_pedidos_cliente_crea_domicilio_recibido_con_iva(gestor):
    pedido = _domicilio(gestor)
    assert pedido.obtener_estado() == "Recibido"
    assert pedido.total == Decimal("28560.00")            # 2 x 12000 x 1,19
    assert pedido.id_pedido is not None


def test_reglas_pedidos_mesero_crea_orden_de_mesa(gestor):
    assert _orden_mesa(gestor).numero_mesa == 2


def test_reglas_pedidos_rol_equivocado_para_el_tipo_da_sin_permiso(gestor):
    with pytest.raises(SinPermisoError):
        gestor.crear_pedido("Cliente", 7, TipoPedido.EN_RESTAURANTE, [ItemPedido(1, 1)], numero_mesa=2)
    with pytest.raises(SinPermisoError):
        gestor.crear_pedido("Mesero", 3, TipoPedido.DOMICILIO, [ItemPedido(1, 1)],
                            "Calle 1", "CONTRA_ENTREGA")


def test_reglas_pedidos_rn05_producto_agotado_se_rechaza(gestor):
    with pytest.raises(ReglaNegocioError):
        gestor.crear_pedido("Cliente", 7, TipoPedido.DOMICILIO, [ItemPedido(2, 1)],
                            "Calle 1", "CONTRA_ENTREGA")
    with pytest.raises(ReglaNegocioError):
        gestor.resumir("Cliente", [ItemPedido(2, 1)])


def test_reglas_pedidos_rn05_producto_disponible_se_acepta(gestor):
    detalle, total = gestor.resumir("Cliente", [ItemPedido(1, 1)])
    assert len(detalle) == 1 and total == Decimal("14280.00")


def test_reglas_pedidos_carrito_vacio_o_cantidad_cero_da_validacion(gestor):
    with pytest.raises(ValidacionError):
        gestor.resumir("Cliente", [])
    with pytest.raises(ValidacionError):
        gestor.resumir("Cliente", [ItemPedido(1, 0)])


def test_reglas_pedidos_producto_inexistente_da_no_encontrado(gestor):
    with pytest.raises(NoEncontradoError):
        gestor.resumir("Cliente", [ItemPedido(99, 1)])


def test_reglas_pedidos_producto_repetido_se_suma_en_una_linea(gestor):
    detalle, _ = gestor.resumir("Cliente", [ItemPedido(1, 1), ItemPedido(1, 2)])
    assert len(detalle) == 1 and detalle[0].cantidad == 3


def test_reglas_pedidos_rn07_cliente_sin_telefono_da_regla_de_negocio(gestor):
    with pytest.raises(ReglaNegocioError):
        _domicilio(gestor, id_cliente=8)


def test_reglas_pedidos_cliente_solo_ve_sus_pedidos(gestor):
    pedido = _domicilio(gestor)
    assert gestor.obtener_pedido("Cliente", 7, pedido.id_pedido) is pedido
    with pytest.raises(SinPermisoError):
        gestor.obtener_pedido("Cliente", 99, pedido.id_pedido)
    with pytest.raises(NoEncontradoError):
        gestor.obtener_pedido("Cliente", 7, 999)


def test_reglas_pedidos_listar_segun_el_rol_y_filtro_de_estado(gestor):
    _domicilio(gestor)
    _orden_mesa(gestor)
    assert len(gestor.listar_pedidos("Cliente", 7)) == 1
    assert len(gestor.listar_pedidos("Mesero", 3)) == 1
    assert gestor.listar_pedidos("Cliente", 7, "EnCocina") == []
    with pytest.raises(ValidacionError):
        gestor.listar_pedidos("Cliente", 7, "Listo")
    with pytest.raises(SinPermisoError):
        gestor.listar_pedidos("Chef", 2)


def test_reglas_pedidos_rn01_modificar_dentro_del_plazo(gestor, reloj):
    pedido = _orden_mesa(gestor)
    reloj.adelantar(4)
    gestor.modificar_pedido("Mesero", 3, pedido.id_pedido, [ItemPedido(1, 3)], numero_mesa=4)
    assert pedido.detalle[0].cantidad == 3 and pedido.numero_mesa == 4


def test_reglas_pedidos_rn01_modificar_pasados_cinco_minutos_se_rechaza(gestor, reloj):
    pedido = _orden_mesa(gestor)
    reloj.adelantar(5)
    with pytest.raises(ReglaNegocioError):
        gestor.modificar_pedido("Mesero", 3, pedido.id_pedido, [ItemPedido(1, 3)])
    assert pedido.detalle[0].cantidad == 1           # no cambió nada


def test_reglas_pedidos_rn04_modificar_en_cocina_se_rechaza(gestor):
    pedido = _orden_mesa(gestor)
    pedido.siguiente()
    with pytest.raises(ReglaNegocioError):
        gestor.modificar_pedido("Mesero", 3, pedido.id_pedido, [ItemPedido(1, 3)])


def test_reglas_pedidos_modificar_valida_agotado_y_mesa_sin_cambiar_nada(gestor):
    pedido = _orden_mesa(gestor)
    with pytest.raises(ReglaNegocioError):
        gestor.modificar_pedido("Mesero", 3, pedido.id_pedido, [ItemPedido(2, 1)])
    with pytest.raises(ValidacionError):
        gestor.modificar_pedido("Mesero", 3, pedido.id_pedido, [ItemPedido(1, 1)], numero_mesa=99)
    assert pedido.numero_mesa == 2


def test_reglas_pedidos_solo_el_mesero_modifica(gestor):
    pedido = _domicilio(gestor)
    with pytest.raises(SinPermisoError):
        gestor.modificar_pedido("Cliente", 7, pedido.id_pedido, [ItemPedido(1, 1)])
    with pytest.raises(SinPermisoError):
        gestor.modificar_pedido("Mesero", 3, pedido.id_pedido, [ItemPedido(1, 1)])   # es domicilio


def test_reglas_pedidos_rn01_cancelar_dentro_del_plazo_elimina_el_pedido(gestor, reloj):
    pedido = _domicilio(gestor)
    reloj.adelantar(4)
    gestor.cancelar_pedido("Cliente", 7, pedido.id_pedido)
    with pytest.raises(NoEncontradoError):
        gestor.obtener_pedido("Cliente", 7, pedido.id_pedido)


def test_reglas_pedidos_rn01_cancelar_pasados_cinco_minutos_no_borra(gestor, reloj, repo):
    pedido = _domicilio(gestor)
    reloj.adelantar(5)
    with pytest.raises(ReglaNegocioError):
        gestor.cancelar_pedido("Cliente", 7, pedido.id_pedido)
    assert pedido.id_pedido in repo.pedidos


def test_reglas_pedidos_rn04_cancelar_en_cocina_se_rechaza(gestor, repo):
    pedido = _domicilio(gestor)
    pedido.siguiente()
    with pytest.raises(ReglaNegocioError):
        gestor.cancelar_pedido("Cliente", 7, pedido.id_pedido)
    assert pedido.id_pedido in repo.pedidos


def test_reglas_pedidos_el_mesero_cancela_ordenes_de_mesa_pero_no_domicilios(gestor):
    orden = _orden_mesa(gestor)
    gestor.cancelar_pedido("Mesero", 3, orden.id_pedido)
    domicilio = _domicilio(gestor)
    with pytest.raises(SinPermisoError):
        gestor.cancelar_pedido("Mesero", 3, domicilio.id_pedido)


def test_reglas_pedidos_domicilio_nace_con_direccion(gestor):
    assert isinstance(_domicilio(gestor), PedidoDomicilio)


# =====================================================================
# Rutas (cliente de pruebas de FastAPI, con el gestor falso)
# =====================================================================

@pytest.fixture
def http(gestor):
    original = app.dependency_overrides.get(rutas_pedidos.obtener_gestor)
    app.dependency_overrides[rutas_pedidos.obtener_gestor] = lambda: gestor
    yield TestClient(app)
    if original is None:
        app.dependency_overrides.pop(rutas_pedidos.obtener_gestor, None)
    else:
        app.dependency_overrides[rutas_pedidos.obtener_gestor] = original


def _cabecera(id_usuario: int, rol: str) -> dict:
    return {"Authorization": f"Bearer {app.state.sesiones.crear(id_usuario, rol)}"}


CUERPO_DOMICILIO = {"tipo_pedido": "DOMICILIO", "direccion": "Calle 10 # 20-30",
                    "metodo_pago": "CONTRA_ENTREGA", "items": [{"id_producto": 1, "cantidad": 2}]}


def test_rutas_pedidos_sin_sesion_da_401(http):
    assert http.get("/api/pedidos").status_code == 401


def test_rutas_pedidos_cliente_crea_domicilio_201_y_nace_recibido(http):
    respuesta = http.post("/api/pedidos", json=CUERPO_DOMICILIO, headers=_cabecera(7, "Cliente"))
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["estado_pedido"] == "Recibido"
    assert datos["total"] == 28560.0
    assert datos["direccion"] == "Calle 10 # 20-30"
    assert datos["detalle"][0]["subtotal"] == 24000.0


def test_rutas_pedidos_falta_el_metodo_de_pago_da_422(http):
    cuerpo = {k: v for k, v in CUERPO_DOMICILIO.items() if k != "metodo_pago"}
    respuesta = http.post("/api/pedidos", json=cuerpo, headers=_cabecera(7, "Cliente"))
    assert respuesta.status_code == 422 and respuesta.json()["errores"]


def test_rutas_pedidos_carrito_vacio_y_cantidad_cero_dan_422(http):
    cabecera = _cabecera(7, "Cliente")
    assert http.post("/api/pedidos", json={**CUERPO_DOMICILIO, "items": []}, headers=cabecera).status_code == 422
    malo = {**CUERPO_DOMICILIO, "items": [{"id_producto": 1, "cantidad": 0}]}
    assert http.post("/api/pedidos", json=malo, headers=cabecera).status_code == 422


def test_rutas_pedidos_producto_agotado_da_409(http):
    cuerpo = {**CUERPO_DOMICILIO, "items": [{"id_producto": 2, "cantidad": 1}]}
    assert http.post("/api/pedidos", json=cuerpo, headers=_cabecera(7, "Cliente")).status_code == 409


def test_rutas_pedidos_cliente_sin_telefono_da_409(http):
    assert http.post("/api/pedidos", json=CUERPO_DOMICILIO, headers=_cabecera(8, "Cliente")).status_code == 409


def test_rutas_pedidos_mesero_no_crea_domicilio_403(http):
    assert http.post("/api/pedidos", json=CUERPO_DOMICILIO, headers=_cabecera(3, "Mesero")).status_code == 403


def test_rutas_pedidos_chef_no_usa_estas_rutas_403(http):
    assert http.get("/api/pedidos", headers=_cabecera(2, "Chef")).status_code == 403


def test_rutas_pedidos_resumen_calcula_el_total_sin_guardar(http, repo):
    cuerpo = {"tipo_pedido": "DOMICILIO", "items": [{"id_producto": 1, "cantidad": 2}]}
    respuesta = http.post("/api/pedidos/resumen", json=cuerpo, headers=_cabecera(7, "Cliente"))
    assert respuesta.status_code == 200 and respuesta.json()["total"] == 28560.0
    assert repo.pedidos == {}


def test_rutas_pedidos_mesero_crea_modifica_y_cancela_una_orden(http, reloj):
    mesero = _cabecera(3, "Mesero")
    creada = http.post("/api/pedidos", headers=mesero, json={
        "tipo_pedido": "EN_RESTAURANTE", "numero_mesa": 2, "items": [{"id_producto": 1, "cantidad": 1}]})
    assert creada.status_code == 201
    id_pedido = creada.json()["id_pedido"]
    nuevo = {"items": [{"id_producto": 1, "cantidad": 3}]}
    assert http.put(f"/api/pedidos/{id_pedido}", json=nuevo, headers=mesero).status_code == 200
    reloj.adelantar(5)
    assert http.put(f"/api/pedidos/{id_pedido}", json=nuevo, headers=mesero).status_code == 409   # RN-01
    assert http.delete(f"/api/pedidos/{id_pedido}", headers=mesero).status_code == 409           # RN-01


def test_rutas_pedidos_cliente_cancela_y_luego_da_404(http):
    cliente = _cabecera(7, "Cliente")
    id_pedido = http.post("/api/pedidos", json=CUERPO_DOMICILIO, headers=cliente).json()["id_pedido"]
    assert http.delete(f"/api/pedidos/{id_pedido}", headers=cliente).status_code == 200
    assert http.get(f"/api/pedidos/{id_pedido}", headers=cliente).status_code == 404


def test_rutas_pedidos_cliente_no_ve_el_pedido_de_otro_403(http):
    id_pedido = http.post("/api/pedidos", json=CUERPO_DOMICILIO,
                          headers=_cabecera(7, "Cliente")).json()["id_pedido"]
    assert http.get(f"/api/pedidos/{id_pedido}", headers=_cabecera(99, "Cliente")).status_code == 403


def test_rutas_pedidos_cliente_no_puede_modificar_403(http):
    cliente = _cabecera(7, "Cliente")
    id_pedido = http.post("/api/pedidos", json=CUERPO_DOMICILIO, headers=cliente).json()["id_pedido"]
    nuevo = {"items": [{"id_producto": 1, "cantidad": 1}]}
    assert http.put(f"/api/pedidos/{id_pedido}", json=nuevo, headers=cliente).status_code == 403


def test_rutas_pedidos_listar_devuelve_total_y_datos(http):
    cliente = _cabecera(7, "Cliente")
    assert http.get("/api/pedidos", headers=cliente).json() == {"total": 0, "datos": []}
    http.post("/api/pedidos", json=CUERPO_DOMICILIO, headers=cliente)
    assert http.get("/api/pedidos", headers=cliente).json()["total"] == 1