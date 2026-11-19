"""
repositorio.py — Contrato de acceso a datos para Notificaciones.

PAPEL EN LA ARQUITECTURA: define las operaciones para leer y actualizar
los avisos simulados guardados en la base de datos. El GestorNotificaciones
depende de esta interfaz (Artículo 5 SOLID).
"""

from abc import ABC, abstractmethod


class IRepositorioAvisos(ABC):

    @abstractmethod
    def listar_por_usuario(
        self, id_usuario: int, leido: bool | None = None
    ) -> list[dict]:
        """Devuelve los avisos de un usuario (opcionalmente filtrados por leído/no leído)."""

    @abstractmethod
    def marcar_como_leido(self, id_aviso: int, id_usuario: int) -> bool:
        """
        Marca como leído un aviso que pertenezca al usuario.
        Devuelve False si el aviso no existe o es de otro usuario.
        """