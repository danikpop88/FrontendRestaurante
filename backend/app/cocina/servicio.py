"""
servicio.py — El "GestorCocina", la capa de negocio del componente.
"""

from typing import List, Optional
from app.cocina.repositorio import IRepositorioCocina
from app.pedidos.repositorio import IRepositorioPedidos
from app.cocina.modelos import ComandoMarcarListo
from app.compartido.reloj import IReloj
from app.compartido.excepciones import ReglaNegocioError, NoEncontradoError


class GestorCocina:
    def __init__(
        self,
        repo_cocina: IRepositorioCocina,
        repo_pedidos: IRepositorioPedidos,
        reloj: IReloj,
    ):
        self.repo_cocina = repo_cocina
        self.repo_pedidos = repo_pedidos
        self.reloj = reloj

    def ver_cola(self, tipo_pedido: Optional[str] = None) -> List:
        return self.repo_cocina.listar_cola(tipo_pedido)

    def tomar_pedido(self, id_pedido: int, id_chef: int):
        pedido = self.repo_pedidos.obtener_por_id(id_pedido)
        if not pedido:
            raise NoEncontradoError("Pedido no encontrado.")

        if pedido.obtener_estado() != "Recibido":
            raise ReglaNegocioError("El pedido no está en estado Recibido.")

        # Pasa a EnCocina y guarda el chef
        pedido.siguiente()  # State Pattern de Fase 5
        pedido.id_chef = id_chef
        self.repo_pedidos.actualizar(pedido)
        return pedido

    def marcar_listo(self, id_pedido: int, id_chef: int):
        pedido = self.repo_pedidos.obtener_por_id(id_pedido)
        if not pedido:
            raise NoEncontradoError("Pedido no encontrado.")

        if pedido.obtener_estado() != "EnCocina":
            raise ReglaNegocioError(
                "El pedido no está en estado EnCocina (no se duplica el aviso)."
            )

        # Ejecuta el patrón Command
        comando = ComandoMarcarListo(pedido, id_chef, self.reloj)
        comando.ejecutar()

        self.repo_pedidos.actualizar(pedido)

        # Nota: La notificación al Observer y la asignación de domiciliario
        # se conectará aquí en el siguiente paso.

        return pedido
