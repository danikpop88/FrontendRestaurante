"""
servicio_ventas.py — El "GestorVentas", capa de negocio del reporte de ventas.

PAPEL EN LA ARQUITECTURA: consulta las ventas (pedidos Entregados con pago
Cobrado) en un rango de fechas. Solo el Administrador puede usarlo (RN-10): esa
regla la exige la ruta con requiere_rol. Depende de IRepositorioVentas, no de
PostgreSQL (Artículo 5). Cuando el rango es inválido lanza ValidacionError y
main.py lo traduce a 422 con la envoltura de los Contratos §0.
"""

from datetime import date
from decimal import Decimal

from app.compartido.excepciones import ValidacionError
from app.ventas_pagos.repositorio_ventas import IRepositorioVentas


class GestorVentas:

    def __init__(self, repositorio: IRepositorioVentas):
        self._repositorio = repositorio

    def consultar_ventas(self, desde: date, hasta: date) -> dict:
        if desde > hasta:
            raise ValidacionError("La fecha 'desde' no puede ser posterior a 'hasta'.")

        registros = self._repositorio.listar_ventas(desde, hasta)
        total_ventas = sum((r.monto for r in registros), Decimal("0"))

        datos = [
            {
                "id_pedido": r.id_pedido,
                "fecha": r.fecha_pedido.isoformat(),
                "total": float(r.total),
                "id_pago": r.id_pago,
                "estado_pago": r.estado_pago,
                "monto": float(r.monto),
                "fecha_pago": r.fecha_pago.isoformat(),
            }
            for r in registros
        ]
        return {
            "desde": desde.isoformat(),
            "hasta": hasta.isoformat(),
            "cantidad": len(datos),
            "total_ventas": float(total_ventas),
            "datos": datos,
        }