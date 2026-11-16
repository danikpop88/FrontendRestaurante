"""
modelos.py — La clase de dominio del componente "Ventas y pagos".

PAPEL EN LA ARQUITECTURA: es la clase Pago del nivel 4 del C4. Solo guarda los
datos de un pago y sabe confirmarse; no contiene SQL (eso es del repositorio)
ni reglas como "no cobrar dos veces" (eso es del servicio, Artículo 3).

Un pago contra entrega nace en "Pendiente de Cobro" y pasa a "Cobrado" cuando
el domiciliario cierra la entrega (RF-07 y RF-21).

Convenciones (Artículo 11): Pago.confirmarPago() del diagrama es confirmar_pago().
El monto es Decimal porque PostgreSQL entrega NUMERIC(12,2) como Decimal.
"""

from datetime import date
from decimal import Decimal

PENDIENTE_DE_COBRO = "Pendiente de Cobro"
COBRADO = "Cobrado"


class Pago:
    """El pago de un pedido."""

    def __init__(self, id_pago: int | None, id_pedido: int, id_cliente: int | None,
                 monto: Decimal, fecha: date, estado_pago: str = PENDIENTE_DE_COBRO):
        self.id_pago = id_pago            # None mientras el pago aún no se guarda en la base
        self.id_pedido = id_pedido
        self.id_cliente = id_cliente      # None en los pagos de pedidos de mesa
        self.monto = monto
        self.fecha = fecha                # se actualiza al registrar el cobro
        self.estado_pago = estado_pago

    def confirmar_pago(self, fecha: date) -> None:
        """Pago.confirmarPago() del diagrama: marca el pago como cobrado en esa fecha."""
        self.estado_pago = COBRADO
        self.fecha = fecha

    def esta_cobrado(self) -> bool:
        return self.estado_pago == COBRADO