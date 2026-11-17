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
        observador_mesero,  # Inyectado
        observador_domiciliario,  # Inyectado
        gestor_domicilios,  # Inyectado de la Fase 6
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

        # 1. Ejecuta el patrón Command (avanza a EnCamino)
        comando = ComandoMarcarListo(pedido, id_chef, self.reloj)
        comando.ejecutar()

        self.repo_pedidos.actualizar(pedido)

        # 2. Patrón Observer: Notificar según el tipo de pedido
        if pedido.tipo_pedido.value == "EN_RESTAURANTE":
            self.observador_mesero.actualizar(pedido)
        else:
            # Es DOMICILIO: Asignar automáticamente (Fase 6) y luego notificar
            # Como el pedido ya cambió a EnCamino, la Fase 6 encontrará su domicilio y lo asignará.
            # (Nota: Para que esto funcione, el GestorDomicilios debe recibir el pedido o su ID)
            domicilio = self.gestor_domicilios.asignar_automaticamente_por_pedido(
                pedido.id_pedido
            )
            if domicilio and domicilio.id_domiciliario:
                # Actualizamos el id del domiciliario en el pedido para que el observador sepa a quién avisar
                pedido.id_domiciliario = domicilio.id_domiciliario
                self.observador_domiciliario.actualizar(pedido)

        return pedido
