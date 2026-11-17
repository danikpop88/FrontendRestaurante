"""
servicio_push.py — El servicio de notificaciones simulado.

PAPEL EN LA ARQUITECTURA: en el MVP, el envío de notificaciones push reales
(RNF-13) está proyectado. Esta clase simula ese servicio externo guardando
el aviso en la tabla 'aviso'. El frontend lo leerá mediante sondeo (polling)
para mostrarlo en pantalla.
"""

from datetime import datetime
from app.compartido.conexion import obtener_conexion


class ServicioPush:
    def __init__(self, conexion):
        self.conexion = conexion

    def enviar_aviso(self, id_usuario: int, mensaje: str) -> None:
        """Guarda el aviso en la base de datos para que el frontend lo lea."""
        sql = """
            INSERT INTO aviso (id_usuario, mensaje, fecha, leido)
            VALUES (%s, %s, %s, %s);
        """
        with self.conexion.cursor() as cur:
            cur.execute(sql, (id_usuario, mensaje, datetime.now(), False))
            self.conexion.commit()
