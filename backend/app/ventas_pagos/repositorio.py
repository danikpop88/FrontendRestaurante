"""
repositorio.py — Contratos de acceso a datos del módulo ventas_pagos.

PAPEL EN LA ARQUITECTURA: son las clases abstractas (ABC) que los servicios
conocen. No saben si detrás hay PostgreSQL o una lista en memoria (pruebas):
dependen de la abstracción (Artículo 5). Aquí no hay reglas de negocio.

  IRepositorioPagos   -> guardar y actualizar pagos (usa ServicioPagoReal)
  IRepositorioVentas  -> consultar las ventas de un rango de fechas (usa GestorVentas)
"""

from abc import ABC, abstractmethod
from datetime import date

from app.ventas_pagos.modelos import Pago


class IRepositorioPagos(ABC):
    """Operaciones de persistencia sobre la tabla pago."""

    @abstractmethod
    def guardar(self, pago: Pago) -> Pago:
        """Guarda un pago nuevo y lo devuelve con su id_pago asignado."""

    @abstractmethod
    def obtener_por_pedido(self, id_pedido: int) -> Pago | None:
        """Devuelve el pago del pedido, o None si no existe."""

    @abstractmethod
    def actualizar(self, pago: Pago) -> None:
        """Guarda el estado y la fecha actuales de un pago que ya existe."""


class IRepositorioVentas(ABC):
    """Consulta de solo lectura sobre pedido y pago."""

    @abstractmethod
    def listar_ventas(self, desde: date, hasta: date) -> list[dict]:
        """
        Devuelve las ventas del rango (ambos extremos incluidos): pedidos
        'Entregado' cuyo pago está 'Cobrado', del más reciente al más antiguo.
        Cada venta es un dict con: id_pedido, fecha, total, id_pago,
        estado_pago, monto y fecha_pago.
        """