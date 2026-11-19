"""
servicio.py — El "GestorCocina", la capa de negocio del componente.
"""

from typing import List, Optional

from app.cocina.repositorio import IRepositorioCocina
from app.pedidos.repositorio import IRepositorioPedidos
from app.cocina.modelos import ComandoMarcarListo
from app.compartido.reloj import IReloj
from app.compartido.excepciones import ReglaNegocioError, NoEncontradoError


def _valor_tipo_pedido(tipo) -> str:
    """Devuelve 'EN_RESTAURANTE' o 'DOMICILIO' venga como enum o como str."""
    return tipo.value if hasattr(tipo, "value") else tipo


class GestorCocina:
    def __init__(
        self,
        repo_cocina: IRepositorioCocina,
        repo_pedidos: IRepositorioPedidos,
        reloj: IReloj,
        observador_mesero,
        observador_domiciliario,
        gestor_domicilios,
    ):
        self.repo_cocina = repo_cocina
        self.repo_pedidos = repo_pedidos
        self.reloj = reloj
        self.observador_mesero = observador_mesero
        self.observador_domiciliario = observador_domiciliario
        self.gestor_domicilios = gestor_domicilios

    def ver_cola(self, tipo_pedido: Optional[str] = None) -> List:
        return self.repo_cocina.listar_cola(tipo_pedido)

    def tomar_pedido(self, id_pedido: int, id_chef: int):
        pedido = self.repo_pedidos.obtener_por_id(id_pedido)
        if not pedido:
            raise NoEncontradoError("Pedido no encontrado.")

        if pedido.obtener_estado() != "Recibido":
            raise ReglaNegocioError("El pedido no está en estado Recibido.")

        pedido.siguiente()
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

        # 1. Patrón Command: avanza a EnCamino y registra quién y cuándo
        comando = ComandoMarcarListo(pedido, id_chef, self.reloj)
        comando.ejecutar()
        self.repo_pedidos.actualizar(pedido)

        # 2. Patrón Observer: notificar según el tipo de pedido
        if _valor_tipo_pedido(pedido.tipo_pedido) == "EN_RESTAURANTE":
            self.observador_mesero.actualizar(pedido)
        else:
            # DOMICILIO: asignar automáticamente (Fase 6) y luego notificar
            domicilio = self.gestor_domicilios.asignar_automaticamente_por_pedido(
                pedido.id_pedido
            )
            if domicilio and domicilio.id_domiciliario:
                # El observador necesita saber a quién avisar. Si IPedido no
                # tiene el atributo id_domiciliario, esto fallará; en ese caso,
                # pasa domicilio al observador en lugar de pedido.
                try:
                    pedido.id_domiciliario = domicilio.id_domiciliario
                except AttributeError:
                    pass
                self.observador_domiciliario.actualizar(pedido)

        return pedido