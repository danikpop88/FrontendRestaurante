"""
servicio_ventas.py — El "GestorVentas", capa de negocio para reportes.

PAPEL EN LA ARQUITECTURA: se encarga de consultar las ventas (pedidos Entregados
con pago Cobrado) en un rango de fechas. Solo el Administrador puede usarlo (RN-10).
"""

from datetime import date
from typing import List, Dict, Any
from app.compartido.conexion import obtener_conexion


class GestorVentas:
    def __init__(self, conexion):
        self.conexion = conexion

    def consultar_ventas(self, desde: date, hasta: date) -> Dict[str, Any]:
        if desde > hasta:
            raise ValueError("La fecha 'desde' no puede ser posterior a 'hasta'.")

        sql = """
            SELECT p.id_pedido, p.fecha, p.total, pa.id_pago, pa.estado_pago, pa.monto, pa.fecha
            FROM pedido p
            JOIN pago pa ON p.id_pedido = pa.id_pedido
            WHERE p.estado_pedido = 'Entregado' 
              AND pa.estado_pago = 'Cobrado'
              AND DATE(p.fecha) >= %s AND DATE(p.fecha) <= %s
            ORDER BY p.fecha DESC;
        """

        datos = []
        total_ventas = 0.0

        with self.conexion.cursor() as cur:
            cur.execute(sql, (desde, hasta))
            for fila in cur.fetchall():
                datos.append(
                    {
                        "id_pedido": fila[0],
                        "fecha": fila[1].isoformat(),
                        "total": float(fila[2]),
                        "id_pago": fila[3],
                        "estado_pago": fila[4],
                        "monto": float(fila[5]),
                        "fecha_pago": fila[6].isoformat(),
                    }
                )
                total_ventas += float(fila[5])

        return {
            "desde": desde.isoformat(),
            "hasta": hasta.isoformat(),
            "cantidad": len(datos),
            "total_ventas": total_ventas,
            "datos": datos,
        }
