"""
repositorio_postgres.py — Implementación del repositorio de Reservas.
"""

from typing import List
from app.reservas.repositorio import IRepositorioReservas
from app.reservas.modelos import Reserva, Mesa
from datetime import date


class RepositorioReservasPostgres(IRepositorioReservas):
    def __init__(self, conexion):
        self.conexion = conexion

    def listar_vigentes(self) -> List[Reserva]:
        sql = """
            SELECT r.id_reserva, r.nombre_titular, r.telefono_titular, 
                   r.fecha_reserva, r.hora_reserva, r.id_cliente,
                   m.id_mesa, m.numero_mesa, m.capacidad_personas, m.disponibilidad
            FROM reserva r
            JOIN mesa m ON r.id_mesa = m.id_mesa
            WHERE r.fecha_reserva >= %s
            ORDER BY r.fecha_reserva ASC, r.hora_reserva ASC;
        """

        reservas = []
        with self.conexion.cursor() as cur:
            cur.execute(sql, (date.today(),))
            for fila in cur.fetchall():
                mesa = Mesa(
                    id_mesa=fila[6],
                    numero_mesa=fila[7],
                    capacidad_personas=fila[8],
                    disponibilidad=fila[9],
                )
                reserva = Reserva(
                    id_reserva=fila[0],
                    mesa=mesa,
                    nombre_titular=fila[1],
                    telefono_titular=fila[2],
                    fecha_reserva=fila[3],
                    hora_reserva=fila[4],
                    id_cliente=fila[5],
                )
                reservas.append(reserva)
        return reservas
