"""
servicio.py — El "GestorReservas", capa de negocio para Reservas.
"""

from typing import List
from app.reservas.repositorio import IRepositorioReservas
from app.reservas.modelos import Reserva


class GestorReservas:
    def __init__(self, repositorio: IRepositorioReservas):
        self.repositorio = repositorio

    def listar_vigentes(self) -> List[Reserva]:
        # Filtramos por si acaso la base trae alguna vencida
        return [r for r in self.repositorio.listar_vigentes() if r.es_vigente()]
