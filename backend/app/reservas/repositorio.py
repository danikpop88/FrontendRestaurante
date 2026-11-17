"""
repositorio.py — Contrato de acceso a datos para Reservas.
"""

from abc import ABC, abstractmethod
from typing import List
from app.reservas.modelos import Reserva


class IRepositorioReservas(ABC):
    @abstractmethod
    def listar_vigentes(self) -> List[Reserva]:
        """Devuelve las reservas desde hoy en adelante."""
        pass
