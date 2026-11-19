"""
repositorio_ventas.py — El contrato de acceso a datos del reporte de ventas.

PAPEL EN LA ARQUITECTURA: es la clase abstracta (ABC) que GestorVentas conoce.
No sabe si detrás hay PostgreSQL o una lista en memoria (pruebas): depende de
la abstracción (Artículo 5). Aquí no hay reglas de negocio.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass
class RegistroVenta:
    """Una venta: un pedido Entregado con su pago Cobrado."""
    id_pedido: int
    fecha_pedido: datetime
    total: Decimal
    id_pago: int
    estado_pago: str
    monto: Decimal
    fecha_pago: date


class IRepositorioVentas(ABC):
    """Consultas de solo lectura para el reporte de ventas."""

    @abstractmethod
    def listar_ventas(self, desde: date, hasta: date) -> list[RegistroVenta]:
        """
        Devuelve los pedidos Entregados con pago Cobrado cuya fecha esté entre
        'desde' y 'hasta' (ambas incluidas), del más reciente al más antiguo.
        """