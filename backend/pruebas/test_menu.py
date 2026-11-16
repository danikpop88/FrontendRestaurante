"""
test_menu.py — Pruebas del módulo "Menú y productos" (Fase 3).

PAPEL EN LA ARQUITECTURA: demuestra que las reglas del GestorMenu (RN-09 y las
validaciones) se cumplen y qué pasa cuando se violan (Artículo 3), y que las
rutas traducen cada caso a su código HTTP. Usa un repositorio FALSO en memoria
(IRepositorioProductos), así que no necesita PostgreSQL: es la prueba de capas.

Cómo correrlas:  pytest pruebas -k menu -v
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.compartido.excepciones import NoEncontradoError, SinPermisoError, ValidacionError
from app.main import app
from app.menu import rutas as rutas_menu
from app.menu.modelos import Producto
from app.menu.repositorio import IRepositorioProductos
from app.menu.servicio import GestorMenu


class RepositorioProductosFalso(IRepositorioProductos):
    """Guarda los productos en un diccionario, con las categorías de datos_ejemplo.sql."""

    def __init__(self):
        self._productos: dict[int, Producto] = {}
        self._siguiente = 1
        self.crear(Producto(None, "Arepa paisa rellena", None, Decimal("12000.00"), "Entradas"))
        self.crear(Producto(None, "Patacón con pollo", None, Decimal("24000.00"), "Platos Fuertes"))
        self.crear(Producto(None, "Copa tres leches", None, Decimal("12000.00"), "Postres"))
        self.crear(Producto(None, "Limonada de panela", None, Decimal("6000.00"), "Bebidas"))

    def listar(self, categoria=None):
        return [p for p in self._productos.values() if categoria is None or p.categoria == categoria]

    def obtener_por_id(self, id_producto):
        return self._productos.get(id_producto)

    def listar_categorias(self):
        return sorted({p.categoria for p in self._productos.values()})

    def crear(self, producto):
        id_producto = self._siguiente
        self._siguiente += 1
        producto.id_producto = id_producto
        self._productos[id_producto] = producto
        return id_producto

    def actualizar(self, producto):
        self._productos[producto.id_producto] = producto


@pytest.fixture
def gestor():
    return GestorMenu(RepositorioProductosFalso())


# =====================================================================
# Reglas del GestorMenu (sin HTTP, sin base de datos)
# =====================================================================

def test_reglas_menu_rn09_administrador_crea_producto(gestor):
    producto = gestor.crear_producto("Administrador", "Postre nuevo", "Postres", Decimal("9000"))
    assert producto.id_producto is not None
    assert producto.disponible is True


@pytest.mark.parametrize("rol", ["Mesero", "Cliente", "Chef", "Domiciliario"])
def test_reglas_menu_rn09_otro_rol_no_modifica_el_menu(gestor, rol):
    with pytest.raises(SinPermisoError):
        gestor.crear_producto(rol, "X", "Postres", Decimal("1"))
    with pytest.raises(SinPermisoError):
        gestor.editar_producto(rol, 1, "X", "Postres", Decimal("1"))
    with pytest.raises(SinPermisoError):
        gestor.cambiar_disponibilidad(rol, 1, False)


def test_reglas_menu_datos_invalidos_devuelven_todos_los_motivos(gestor):
    with pytest.raises(ValidacionError) as excepcion:
        gestor.crear_producto("Administrador", "   ", "Inexistente", Decimal("-5"))
    assert len(excepcion.value.errores) == 3


def test_reglas_menu_precio_cero_es_valido(gestor):
    producto = gestor.crear_producto("Administrador", "Cortesía", "Bebidas", Decimal("0"))
    assert producto.precio == Decimal("0")


def test_reglas_menu_categoria_inexistente_se_rechaza_al_editar(gestor):
    with pytest.raises(ValidacionError):
        gestor.editar_producto("Administrador", 1, "Arepa", "Sopas", Decimal("12000"))


def test_reglas_menu_editar_producto_inexistente_da_no_encontrado(gestor):
    with pytest.raises(NoEncontradoError):
        gestor.editar_producto("Administrador", 999, "X", "Postres", Decimal("1"))


def test_reglas_menu_editar_no_cambia_la_disponibilidad(gestor):
    gestor.cambiar_disponibilidad("Administrador", 1, False)
    gestor.editar_producto("Administrador", 1, "Arepa editada", "Entradas", Decimal("13000"))
    producto = gestor.listar_productos("Entradas")[0]
    assert producto.nombre == "Arepa editada"
    assert producto.disponible is False


def test_reglas_menu_marcar_agotado_y_volver_a_disponible(gestor):
    gestor.cambiar_disponibilidad("Administrador", 1, False)
    assert gestor.listar_productos("Entradas")[0].disponible is False
    gestor.cambiar_disponibilidad("Administrador", 1, True)
    assert gestor.listar_productos("Entradas")[0].disponible is True


def test_reglas_menu_filtra_por_categoria_y_categoria_vacia_no_es_error(gestor):
    assert len(gestor.listar_productos("Postres")) == 1
    assert gestor.listar_productos("Sopas") == []


# =====================================================================
# Rutas (cliente de pruebas de FastAPI, con el gestor falso)
# =====================================================================

@pytest.fixture
def http(gestor):
    original = app.dependency_overrides.get(rutas_menu.obtener_gestor)
    app.dependency_overrides[rutas_menu.obtener_gestor] = lambda: gestor
    yield TestClient(app)
    if original is None:
        app.dependency_overrides.pop(rutas_menu.obtener_gestor, None)
    else:
        app.dependency_overrides[rutas_menu.obtener_gestor] = original


def _cabecera(rol: str) -> dict:
    token = app.state.sesiones.crear(1, rol)
    return {"Authorization": f"Bearer {token}"}


def test_rutas_menu_sin_sesion_da_401(http):
    assert http.get("/api/menu/productos").status_code == 401


def test_rutas_menu_cliente_consulta_el_menu_y_filtra(http):
    respuesta = http.get("/api/menu/productos", headers=_cabecera("Cliente"))
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 4
    filtrada = http.get("/api/menu/productos?categoria=Postres", headers=_cabecera("Cliente"))
    assert filtrada.json()["total"] == 1
    vacia = http.get("/api/menu/productos?categoria=Sopas", headers=_cabecera("Cliente"))
    assert vacia.status_code == 200 and vacia.json()["datos"] == []


def test_rutas_menu_administrador_crea_producto_201(http):
    cuerpo = {"nombre": "Flan", "categoria": "Postres", "precio": 9500.5, "descripcion": "Con caramelo"}
    respuesta = http.post("/api/menu/productos", json=cuerpo, headers=_cabecera("Administrador"))
    assert respuesta.status_code == 201
    assert respuesta.json()["id_producto"] is not None


def test_rutas_menu_mesero_no_crea_productos_403(http):
    cuerpo = {"nombre": "Flan", "categoria": "Postres", "precio": 9500}
    respuesta = http.post("/api/menu/productos", json=cuerpo, headers=_cabecera("Mesero"))
    assert respuesta.status_code == 403


def test_rutas_menu_nombre_vacio_y_precio_negativo_dan_422_con_motivos(http):
    cuerpo = {"nombre": "", "categoria": "Postres", "precio": -5}
    respuesta = http.post("/api/menu/productos", json=cuerpo, headers=_cabecera("Administrador"))
    assert respuesta.status_code == 422
    assert len(respuesta.json()["errores"]) == 2


def test_rutas_menu_categoria_inexistente_da_422(http):
    cuerpo = {"nombre": "Sopa", "categoria": "Sopas", "precio": 7000}
    respuesta = http.post("/api/menu/productos", json=cuerpo, headers=_cabecera("Administrador"))
    assert respuesta.status_code == 422
    assert "La categoría no existe en el menú." in respuesta.json()["errores"]


def test_rutas_menu_editar_producto_200_y_404(http):
    cuerpo = {"nombre": "Arepa", "categoria": "Entradas", "precio": 13000, "descripcion": "Con queso"}
    assert http.put("/api/menu/productos/1", json=cuerpo, headers=_cabecera("Administrador")).status_code == 200
    assert http.put("/api/menu/productos/999", json=cuerpo, headers=_cabecera("Administrador")).status_code == 404


def test_rutas_menu_marcar_agotado_y_validar_el_booleano(http):
    admin = _cabecera("Administrador")
    ok = http.patch("/api/menu/productos/1/disponibilidad", json={"disponible": False}, headers=admin)
    assert ok.status_code == 200
    producto = http.get("/api/menu/productos?categoria=Entradas", headers=admin).json()["datos"][0]
    assert producto["disponible"] is False
    assert http.patch("/api/menu/productos/1/disponibilidad", json={}, headers=admin).status_code == 422
    assert http.patch("/api/menu/productos/1/disponibilidad", json={"disponible": "no"}, headers=admin).status_code == 422
    assert http.patch("/api/menu/productos/999/disponibilidad", json={"disponible": False}, headers=admin).status_code == 404