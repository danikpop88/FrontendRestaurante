"""
rutas.py — Las cinco rutas HTTP de los pedidos (Contratos §3).

PAPEL EN LA ARQUITECTURA: es la capa de rutas (el controlador) del componente
"Pedidos". Recibe la petición, valida su FORMA con Pydantic (tipos y campos
obligatorios: si falla, 422), exige sesión y rol, y delega en el GestorPedidos.
No contiene reglas de negocio ni SQL (Artículos 2 y 3). El formato JSON del
pedido vive en pedidos/respuestas.py, compartido con las rutas de cocina.

Rutas (todas bajo /api/pedidos):
    POST   /resumen        Cliente, Mesero   total y detalle sin guardar  RF-03, RF-04
    POST   ""              Cliente, Mesero   hacer el pedido (201)        RF-03, 06, 07, 16
    GET    ""              Cliente, Mesero   mis pedidos / órdenes de mesa RF-05, RF-16
    GET    /{id_pedido}    Cliente, Mesero   el estado de un pedido       RF-05
    PUT    /{id_pedido}    Mesero            modificar una orden de mesa  RF-16
    DELETE /{id_pedido}    Cliente, Mesero   cancelar (elimina el pedido) RF-05, RF-16

Cómo obtiene el gestor: igual que los otros módulos. La ruta pide obtener_gestor()
y main.py, el punto único de ensamblaje, la reemplaza con dependency_overrides.
"""

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.compartido.seguridad import Sesion, requiere_rol
from app.pedidos.modelos import TipoPedido
from app.pedidos.respuestas import detalle_json as _detalle_json
from app.pedidos.respuestas import pedido_json as _pedido_json
from app.pedidos.servicio import GestorPedidos, ItemPedido

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])


def obtener_gestor() -> GestorPedidos:
    """Marcador: main.py lo reemplaza por la función que arma el gestor real."""
    raise NotImplementedError("main.py debe ensamblar el GestorPedidos.")


# =====================================================================
# Cuerpos de las peticiones
# =====================================================================

class ItemEntrada(BaseModel):
    id_producto: int
    cantidad: int                      # que sea >= 1 lo valida el gestor (422)
    observaciones_especiales: str | None = Field(default=None, max_length=300)


class PedidoEntrada(BaseModel):
    """Cuerpo para crear o resumir un pedido (Contratos §3)."""
    tipo_pedido: Literal["DOMICILIO", "EN_RESTAURANTE"]
    items: list[ItemEntrada]
    direccion: str | None = None
    metodo_pago: str | None = None
    numero_mesa: int | None = None


class ModificarEntrada(BaseModel):
    items: list[ItemEntrada]
    numero_mesa: int | None = None


def _a_items(items: list[ItemEntrada]) -> list[ItemPedido]:
    return [ItemPedido(i.id_producto, i.cantidad, i.observaciones_especiales) for i in items]


# =====================================================================
# Rutas
# =====================================================================

@router.post("/resumen")
def resumir_pedido(
    cuerpo: PedidoEntrada,
    gestor: GestorPedidos = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol("Cliente", "Mesero")),
):
    detalle, total = gestor.resumir(sesion.rol, _a_items(cuerpo.items))
    return {"total": float(total), "detalle": [_detalle_json(d) for d in detalle]}


@router.post("", status_code=201)
def crear_pedido(
    cuerpo: PedidoEntrada,
    gestor: GestorPedidos = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol("Cliente", "Mesero")),
):
    pedido = gestor.crear_pedido(
        sesion.rol, sesion.id_usuario, TipoPedido(cuerpo.tipo_pedido), _a_items(cuerpo.items),
        cuerpo.direccion, cuerpo.metodo_pago, cuerpo.numero_mesa,
    )
    return _pedido_json(pedido)


@router.get("")
def listar_pedidos(
    estado_pedido: str | None = None,
    gestor: GestorPedidos = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol("Cliente", "Mesero")),
):
    pedidos = gestor.listar_pedidos(sesion.rol, sesion.id_usuario, estado_pedido)
    return {"total": len(pedidos), "datos": [_pedido_json(p) for p in pedidos]}


@router.get("/{id_pedido}")
def obtener_pedido(
    id_pedido: int,
    gestor: GestorPedidos = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol("Cliente", "Mesero")),
):
    return _pedido_json(gestor.obtener_pedido(sesion.rol, sesion.id_usuario, id_pedido))


@router.put("/{id_pedido}")
def modificar_pedido(
    id_pedido: int,
    cuerpo: ModificarEntrada,
    gestor: GestorPedidos = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol("Mesero")),
):
    pedido = gestor.modificar_pedido(
        sesion.rol, sesion.id_usuario, id_pedido, _a_items(cuerpo.items), cuerpo.numero_mesa,
    )
    return _pedido_json(pedido)


@router.delete("/{id_pedido}")
def cancelar_pedido(
    id_pedido: int,
    gestor: GestorPedidos = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol("Cliente", "Mesero")),
):
    gestor.cancelar_pedido(sesion.rol, sesion.id_usuario, id_pedido)
    return {"estado": 200, "mensaje": "Pedido cancelado."}