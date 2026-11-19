"""
servicio_ventas.py — GestorVentas, la capa de negocio del reporte de ventas.

PAPEL EN LA ARQUITECTURA: valida el rango de fechas y calcula el total de las
ventas (un pedido 'Entregado' con pago 'Cobrado'). No escribe SQL: pide los datos
a un IRepositorioVentas (Artículo 5). El rol Administrador (RN-10) lo exige la
ruta con requiere_rol.
"""

from datetime import date

from app.compartido.excepciones import ValidacionError
from app.ventas_pagos.repositorio import IRepositorioVentas


class GestorVentas:

    def __init__(self, repositorio: IRepositorioVentas):
        self._repositorio = repositorio

    def consultar_ventas(self, desde: date, hasta: date) -> dict:
        """Ventas del rango con su total. 'desde' posterior a 'hasta' -> 422."""
        if desde > hasta:
            raise ValidacionError("La fecha 'desde' no puede ser posterior a 'hasta'.")
        ventas = self._repositorio.listar_ventas(desde, hasta)
        total_ventas = round(sum(float(v["monto"]) for v in ventas), 2)
        return {
            "desde": desde.isoformat(),
            "hasta": hasta.isoformat(),
            "cantidad": len(ventas),
            "total_ventas": total_ventas,
            "datos": ventas,
        }