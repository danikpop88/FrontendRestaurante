"""
modelos.py — Clases de dominio para el componente Reservas.
"""

from datetime import date, time
from abc import ABC, abstractmethod


class IVerificable(ABC):
    @abstractmethod
    def es_vigente(self) -> bool:
        """Verifica si la reserva está en curso o es futura."""
        pass


class Mesa:
    def __init__(
        self,
        id_mesa: int,
        numero_mesa: int,
        capacidad_personas: int,
        disponibilidad: bool,
    ):
        self.id_mesa = id_mesa
        self.numero_mesa = numero_mesa
        self.capacidad_personas = capacidad_personas
        self.disponibilidad = disponibilidad


class Reserva(IVerificable):
    def __init__(
        self,
        id_reserva: int,
        mesa: Mesa,
        nombre_titular: str,
        telefono_titular: str,
        fecha_reserva: date,
        hora_reserva: time,
        id_cliente: int | None = None,
    ):
        self.id_reserva = id_reserva
        self.mesa = mesa
        self.nombre_titular = nombre_titular
        self.telefono_titular = telefono_titular
        self.fecha_reserva = fecha_reserva
        self.hora_reserva = hora_reserva
        self.id_cliente = id_cliente

    def es_vigente(self) -> bool:
        return self.fecha_reserva >= date.today()
