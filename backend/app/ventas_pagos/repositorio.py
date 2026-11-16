"""
repositorio.py — El contrato de acceso a datos de los pagos.

PAPEL EN LA ARQUITECTURA: es la clase abstracta (ABC) que ServicioPagoReal
conoce. No sabe si detrás hay PostgreSQL o una lista en memoria (pruebas):
depende de la abstracción (Artículo 5). Aquí no hay reglas de negocio.
"""

from abc import ABC, abstractmethod

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