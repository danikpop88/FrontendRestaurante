"""
repositorio_ventas_postgres.py — Implementación de IRepositorioVentas con psycopg 3.

PAPEL EN LA ARQUITECTURA: es la pieza del reporte de ventas que escribe SQL
(Artículo 2). Consulta parametrizada (%s con tupla), nunca concatenada
(Artículo 6). Solo lee; la regla del rango de fechas está en el servicio.
"""

from datetime import date

from app.ventas_pagos.repositorio_ventas import IRepositorioVentas, RegistroVenta


class RepositorioVentasPostgres(IRepositorioVentas):

    def __init__(self, conexion):
        self._conexion = conexion

    def listar_ventas(self, desde: date, hasta: date) -> list[RegistroVenta]:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                "SELECT p.id_pedido, p.fecha, p.total, "
                "       pa.id_pago, pa.estado_pago, pa.monto, pa.fecha "
                "FROM pedido p "
                "JOIN pago pa ON pa.id_pedido = p.id_pedido "
                "WHERE p.estado_pedido = 'Entregado' "
                "  AND pa.estado_pago = 'Cobrado' "
                "  AND DATE(p.fecha) >= %s AND DATE(p.fecha) <= %s "
                "ORDER BY p.fecha DESC",
                (desde, hasta),
            )
            filas = cursor.fetchall()
        return [
            RegistroVenta(
                id_pedido=f[0], fecha_pedido=f[1], total=f[2],
                id_pago=f[3], estado_pago=f[4], monto=f[5], fecha_pago=f[6],
            )
            for f in filas
        ]