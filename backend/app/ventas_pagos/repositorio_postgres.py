"""
repositorio_postgres.py — Implementaciones con psycopg 3 de los repositorios
del módulo ventas_pagos.

PAPEL EN LA ARQUITECTURA: es la ÚNICA pieza del módulo ventas_pagos/ que escribe
SQL (Artículo 2). Consultas parametrizadas (%s con tupla), nunca concatenadas
(Artículo 6). Solo guarda y lee; las reglas están en los servicios.

Las escrituras terminan con commit(); si algo falla antes, la conexión se cierra
y PostgreSQL descarta los cambios pendientes.
"""

from datetime import date

from app.ventas_pagos.modelos import Pago
from app.ventas_pagos.repositorio import IRepositorioPagos, IRepositorioVentas

_COLUMNAS = "id_pago, id_pedido, id_cliente, monto, fecha, estado_pago"


class RepositorioPagosPostgres(IRepositorioPagos):

    def __init__(self, conexion):
        self._conexion = conexion

    def guardar(self, pago: Pago) -> Pago:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO pago (id_pedido, id_cliente, estado_pago, fecha, monto) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id_pago",
                (pago.id_pedido, pago.id_cliente, pago.estado_pago, pago.fecha, pago.monto),
            )
            pago.id_pago = cursor.fetchone()[0]
        self._conexion.commit()
        return pago

    def obtener_por_pedido(self, id_pedido: int) -> Pago | None:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT {_COLUMNAS} FROM pago WHERE id_pedido = %s",
                (id_pedido,),
            )
            fila = cursor.fetchone()
        if fila is None:
            return None
        return Pago(id_pago=fila[0], id_pedido=fila[1], id_cliente=fila[2],
                    monto=fila[3], fecha=fila[4], estado_pago=fila[5])

    def actualizar(self, pago: Pago) -> None:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE pago SET estado_pago = %s, fecha = %s WHERE id_pago = %s",
                (pago.estado_pago, pago.fecha, pago.id_pago),
            )
        self._conexion.commit()


class RepositorioVentasPostgres(IRepositorioVentas):

    def __init__(self, conexion):
        self._conexion = conexion

    def listar_ventas(self, desde: date, hasta: date) -> list[dict]:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                "SELECT p.id_pedido, p.fecha, p.total, "
                "       pa.id_pago, pa.estado_pago, pa.monto, pa.fecha "
                "FROM pedido p "
                "JOIN pago pa ON pa.id_pedido = p.id_pedido "
                "WHERE p.estado_pedido = %s AND pa.estado_pago = %s "
                "  AND DATE(p.fecha) >= %s AND DATE(p.fecha) <= %s "
                "ORDER BY p.fecha DESC",
                ("Entregado", "Cobrado", desde, hasta),
            )
            filas = cursor.fetchall()
        return [
            {
                "id_pedido": f[0],
                "fecha": f[1],
                "total": f[2],
                "id_pago": f[3],
                "estado_pago": f[4],
                "monto": f[5],
                "fecha_pago": f[6],
            }
            for f in filas
        ]