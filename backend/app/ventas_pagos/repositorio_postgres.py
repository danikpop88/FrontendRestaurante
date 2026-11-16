"""
repositorio_postgres.py — Implementación de IRepositorioPagos con psycopg 3.

PAPEL EN LA ARQUITECTURA: es la ÚNICA pieza del módulo ventas_pagos/ que escribe
SQL (Artículo 2). Consultas parametrizadas (%s con tupla), nunca concatenadas
(Artículo 6). Solo guarda y lee; las reglas están en el servicio.

Las escrituras terminan con commit(); si algo falla antes, la conexión se cierra
y PostgreSQL descarta los cambios pendientes.
"""

from app.ventas_pagos.modelos import Pago
from app.ventas_pagos.repositorio import IRepositorioPagos

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