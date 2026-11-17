"""
repositorio.py — Contrato de acceso a datos para Cocina.
"""

from abc import ABC, abstractmethod
from typing import List
from app.pedidos.modelos import IPedido


class IRepositorioCocina(ABC):
    @abstractmethod
    def listar_cola(self, tipo_pedido: str | None = None) -> List[IPedido]:
        """Devuelve los pedidos Recibido y EnCocina ordenados por llegada."""
        pass
