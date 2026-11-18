"""
servicio.py — GestorNotificaciones, la capa de negocio de los avisos.

PAPEL EN LA ARQUITECTURA: entre la ruta y el repositorio. Lista los avisos de
quien consulta y marca como leído solo un aviso que sea suyo: si no existe o es
de otro usuario responde NoEncontradoError (404), sin revelar cuál de los dos
casos fue (Contratos §6). No escribe SQL: depende de IRepositorioAvisos.
"""

from app.compartido.excepciones import NoEncontradoError
from app.notificaciones.repositorio import IRepositorioAvisos


class GestorNotificaciones:

    def __init__(self, repositorio: IRepositorioAvisos):
        self._repositorio = repositorio

    def listar_avisos(self, id_usuario: int, leido: bool | None = None) -> list[dict]:
        """Los avisos del usuario, del más reciente al más antiguo."""
        return self._repositorio.listar_por_usuario(id_usuario, leido)

    def marcar_como_leido(self, id_aviso: int, id_usuario: int) -> None:
        """Marca un aviso propio como leído; si no es suyo o no existe -> 404."""
        if not self._repositorio.marcar_como_leido(id_aviso, id_usuario):
            raise NoEncontradoError("El aviso no existe.")