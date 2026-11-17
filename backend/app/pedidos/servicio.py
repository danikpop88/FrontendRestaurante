"""
servicio.py — GestorPedidos: las reglas de negocio del componente "Pedidos".

PAPEL EN LA ARQUITECTURA: es la capa de negocio del módulo (Artículo 3). No
conoce HTTP ni SQL: recibe datos ya tipados desde la ruta, aplica las reglas y
pide al repositorio (contrato IRepositorioPedidos) que guarde o lea. Coordina
dos patrones sin conocer sus clases concretas (Artículo 5):

    Factory Method -> recibe un mapa TipoPedido -> ICreadorPedidos y llama
                      crear_pedido(); no usa new ni if para elegir el tipo.
    State          -> las reglas RN-01 y RN-04 viven en los estados; el gestor
                      solo pregunta pedido.modificar(reloj) / pedido.cancelar(reloj).

Reglas que aplica el gestor:
  - Quién puede qué (SinPermisoError -> 403): un Cliente solo crea pedidos a
    domicilio y solo ve o cancela los suyos; un Mesero solo crea, ve, modifica y
    cancela órdenes de mesa.
  - Carrito (ValidacionError -> 422): no vacío y cantidades >= 1.
  - Producto inexistente (NoEncontradoError -> 404).
  - RN-05: un producto "Agotado" no se puede pedir (ReglaNegocioError -> 409).
  - RN-01 y RN-04: las aplican los estados (409).
  - RN-07 y la mesa existente: las aplican los creadores.

El IServicioPago (el Proxy de pago) se recibe aquí por inyección (Plan §5.11).
Crear el pedido ya inserta su pago 'Pendiente de Cobro' en la misma transacción
del repositorio; el cobro lo usa GestorDomicilios (Fase 6) al cerrar la entrega.

Cancelar elimina el pedido (decisión D20): el estado autoriza, el repositorio borra.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.compartido.excepciones import (
    NoEncontradoError,
    ReglaNegocioError,
    SinPermisoError,
    ValidacionError,
)
from app.compartido.reloj import IReloj
from app.menu.repositorio import IRepositorioProductos
from app.pedidos.creadores.creador_pedidos import DatosPedido, ICreadorPedidos
from app.pedidos.modelos import DetallePedido, IPedido, PedidoMesa, TipoPedido
from app.pedidos.repositorio import IRepositorioPedidos
from app.ventas_pagos.servicio import IServicioPago

ROL_CLIENTE = "Cliente"
ROL_MESERO = "Mesero"
ESTADOS_VALIDOS = ("Recibido", "EnCocina", "EnCamino", "Entregado")

# Qué tipo de pedido puede crear cada rol.
_TIPO_POR_ROL = {
    ROL_CLIENTE: TipoPedido.DOMICILIO,
    ROL_MESERO: TipoPedido.EN_RESTAURANTE,
}


@dataclass
class ItemPedido:
    """Una línea que pide el usuario: qué producto y cuántas unidades."""
    id_producto: int
    cantidad: int
    observaciones_especiales: str | None = None


class GestorPedidos:

    def __init__(self, repositorio: IRepositorioPedidos,
                 repositorio_productos: IRepositorioProductos,
                 creadores: dict[TipoPedido, ICreadorPedidos],
                 servicio_pago: IServicioPago, reloj: IReloj):
        self._repositorio = repositorio
        self._productos = repositorio_productos
        self._creadores = creadores              # TipoPedido -> creador (lo arma main.py)
        self._servicio_pago = servicio_pago      # el Proxy; lo usa el cobro (Fase 6)
        self._reloj = reloj

    # ------------------------------------------------------- resumen (RF-03, RF-04)
    def resumir(self, rol: str, items: list[ItemPedido]) -> tuple[list[DetallePedido], Decimal]:
        """Devuelve el detalle y el total con IVA, sin guardar nada."""
        if rol not in _TIPO_POR_ROL:
            raise SinPermisoError("No tiene permiso para realizar esta acción.")
        detalle = self._construir_detalle(items)
        temporal = PedidoMesa(None, self._reloj.ahora(), 0, detalle=detalle)   # solo para calcular
        return detalle, temporal.total

    # ------------------------------------------------------- crear (RF-03, 06, 07, 16)
    def crear_pedido(self, rol: str, id_usuario: int, tipo: TipoPedido, items: list[ItemPedido],
                     direccion: str | None = None, metodo_pago: str | None = None,
                     numero_mesa: int | None = None) -> IPedido:
        """GestorPedidos.crearPedido(tipo, datos): el pedido nace en Recibido."""
        if _TIPO_POR_ROL.get(rol) != tipo:
            raise SinPermisoError("Su rol no puede crear este tipo de pedido.")
        detalle = self._construir_detalle(items)
        datos = DatosPedido(
            detalle=detalle,
            id_cliente=id_usuario if rol == ROL_CLIENTE else None,
            direccion=direccion, metodo_pago=metodo_pago, numero_mesa=numero_mesa,
        )
        pedido = self._creadores[tipo].crear_pedido(datos)       # Factory Method
        return self._repositorio.crear(pedido)

    # ------------------------------------------------------- consultas (RF-05, RF-16)
    def listar_pedidos(self, rol: str, id_usuario: int,
                       estado_pedido: str | None = None) -> list[IPedido]:
        if estado_pedido is not None and estado_pedido not in ESTADOS_VALIDOS:
            raise ValidacionError("El estado indicado no es válido.")
        if rol == ROL_CLIENTE:
            return self._repositorio.listar_de_cliente(id_usuario, estado_pedido)
        if rol == ROL_MESERO:
            return self._repositorio.listar_de_mesa(estado_pedido)
        raise SinPermisoError("No tiene permiso para realizar esta acción.")

    def obtener_pedido(self, rol: str, id_usuario: int, id_pedido: int) -> IPedido:
        pedido = self._obtener(id_pedido)
        self._exigir_acceso(rol, id_usuario, pedido)
        return pedido

    # ------------------------------------------------------- modificar (RF-16)
    def modificar_pedido(self, rol: str, id_usuario: int, id_pedido: int,
                         items: list[ItemPedido], numero_mesa: int | None = None) -> IPedido:
        """El mesero reemplaza la lista de productos (y, si quiere, la mesa) de una orden."""
        if rol != ROL_MESERO:
            raise SinPermisoError("Solo el mesero modifica órdenes de mesa.")
        pedido = self._obtener(id_pedido)
        self._exigir_acceso(rol, id_usuario, pedido)
        pedido.modificar(self._reloj)                            # State: RN-01 y RN-04
        detalle = self._construir_detalle(items)                 # RN-05
        if numero_mesa is not None and numero_mesa != pedido.numero_mesa:
            if not self._repositorio.existe_mesa(numero_mesa):
                raise ValidacionError("La mesa indicada no existe.")
            pedido.numero_mesa = numero_mesa
        pedido.reemplazar_detalle(detalle)
        self._repositorio.actualizar(pedido)
        return pedido

    # ------------------------------------------------------- cancelar (RF-05, RF-16)
    def cancelar_pedido(self, rol: str, id_usuario: int, id_pedido: int) -> None:
        """Cancelar elimina el pedido. El estado decide si se puede (RN-01 y RN-04)."""
        pedido = self._obtener(id_pedido)
        self._exigir_acceso(rol, id_usuario, pedido)
        if pedido.cancelar(self._reloj):                         # State: lanza 409 si no se puede
            self._repositorio.eliminar(id_pedido)

    # ------------------------------------------------------- internos
    def _obtener(self, id_pedido: int) -> IPedido:
        pedido = self._repositorio.obtener_por_id(id_pedido)
        if pedido is None:
            raise NoEncontradoError("El pedido no existe.")
        return pedido

    def _exigir_acceso(self, rol: str, id_usuario: int, pedido: IPedido) -> None:
        """Cliente: solo sus pedidos. Mesero: solo órdenes de mesa. Otro rol: nada."""
        if rol == ROL_CLIENTE and pedido.id_cliente == id_usuario:
            return
        if rol == ROL_MESERO and pedido.obtener_tipo() == TipoPedido.EN_RESTAURANTE:
            return
        raise SinPermisoError("No tiene permiso para ver o cambiar este pedido.")

    def _construir_detalle(self, items: list[ItemPedido]) -> list[DetallePedido]:
        """Valida el carrito y arma las líneas con el precio actual (RN-05)."""
        if not items:
            raise ValidacionError("El carrito está vacío.")
        if any(item.cantidad < 1 for item in items):
            raise ValidacionError("La cantidad de cada producto debe ser al menos 1.")
        detalle: dict[int, DetallePedido] = {}
        for item in items:
            producto = self._productos.obtener_por_id(item.id_producto)
            if producto is None:
                raise NoEncontradoError(f"El producto {item.id_producto} no existe.")
            if not producto.disponible:
                raise ReglaNegocioError(f"El producto '{producto.nombre}' está agotado.")   # RN-05
            if item.id_producto in detalle:                      # producto repetido: se suman
                existente = detalle[item.id_producto]
                existente.cantidad += item.cantidad
                if item.observaciones_especiales is not None:
                    existente.observaciones_especiales = item.observaciones_especiales
            else:
                detalle[item.id_producto] = DetallePedido(
                    producto.id_producto, producto.nombre, item.cantidad,
                    producto.precio, item.observaciones_especiales,
                )
        return list(detalle.values())