"""
repositorio.py — Contrato de acceso a datos para Notificaciones.

PAPEL EN LA ARQUITECTURA: define las operaciones para leer y actualizar
los avisos simulados guardados en la base de datos. El GestorNotificaciones
dependerá de esta interfaz (Artículo 5 SOLID).
"""

from abc import ABC, abstractmethod
from typing import List
from app.compartido.modelos import (
    Aviso,
)  # Asumiendo que el modelo Aviso está en compartido o lo creamos aquí abajo


class IRepositorioAvisos(ABC):
    @abstractmethod
    def listar_por_usuario(
        self, id_usuario: int, leido: bool | None = None
    ) -> List[dict]:
        """Devuelve los avisos de un usuario (opcionalmente filtrados por leído/no leído)."""
        pass

    @abstractmethod
    def marcar_como_leido(self, id_aviso: int, id_usuario: int) -> None:
        """Marca un aviso como leído, validando que pertenezca al usuario."""
        pass
