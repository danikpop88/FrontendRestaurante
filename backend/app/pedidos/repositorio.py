"""
repositorio.py — El contrato de acceso a datos de los pedidos.

PAPEL EN LA ARQUITECTURA: es la clase abstracta (ABC) que GestorPedidos conoce.
No sabe si detrás hay PostgreSQL o una lista en memoria (pruebas): depende de la
abstracción (Artículo 5). Los métodos reciben y devuelven clases de dominio
(PedidoMesa, PedidoDomicilio), no filas sueltas. Aquí no hay reglas de negocio.

Además de guardar y leer pedidos, ofrece dos consultas pequeñas que main.py
entrega a los creadores como funciones (Factory Method sin SQL propio):
obtener_telefono_cliente (RN-07) y existe_mesa.

Cambiar el estado de un pedido y guardar quién es el chef llegan con el módulo
de Cocina (Fase 7).
"""

from abc import ABC, abstractmethod

from app.pedidos.modelos import IPedido


class IRepositorioPedidos(ABC):
    """Operaciones de persistencia sobre pedido, detalle_pedido, domicilio y pago."""

    @abstractmethod
    def crear(self, pedido: IPedido) -> IPedido:
        """
        Guarda el pedido con su detalle y, si es a domicilio, su domicilio (sin
        domiciliario) y su pago 'Pendiente de Cobro', todo en UNA transacción.
        Devuelve el pedido con su id_pedido asignado.
        """

    @abstractmethod
    def obtener_por_id(self, id_pedido: int) -> IPedido | None:
        """Devuelve el pedido con su detalle, o None si no existe."""

    @abstractmethod
    def listar_de_cliente(self, id_cliente: int, estado_pedido: str | None = None) -> list[IPedido]:
        """Los pedidos del cliente, del más reciente al más antiguo; filtro opcional por estado."""

    @abstractmethod
    def listar_de_mesa(self, estado_pedido: str | None = None) -> list[IPedido]:
        """Las órdenes de mesa, de la más reciente a la más antigua; filtro opcional por estado."""

    @abstractmethod
    def actualizar(self, pedido: IPedido) -> None:
        """Guarda el detalle, el total y la mesa de un pedido modificado, en UNA transacción."""

    @abstractmethod
    def eliminar(self, id_pedido: int) -> None:
        """Cancelar: borra el pedido con su detalle, su domicilio y su pago, en UNA transacción."""

    @abstractmethod
    def obtener_telefono_cliente(self, id_cliente: int) -> str | None:
        """Devuelve el teléfono del usuario, o None si no existe (lo usa RN-07)."""

    @abstractmethod
    def existe_mesa(self, numero_mesa: int) -> bool:
        """Dice si hay una mesa con ese número."""