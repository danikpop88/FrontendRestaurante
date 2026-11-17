"""
modelos.py — Los observadores del Patrón Observer.

PAPEL EN LA ARQUITECTURA: cuando un pedido cambia de estado a "EnCamino",
notifica a sus observadores. Los observadores concretos son el Mesero (para
pedidos de mesa) y el Domiciliario (para pedidos a domicilio). Ellos reciben
el pedido y usan el ServicioPush para generar el aviso.
"""

from abc import ABC, abstractmethod
from app.pedidos.modelos import IPedido
from app.integraciones.servicio_push import ServicioPush


class IObservadorPedido(ABC):
    @abstractmethod
    def actualizar(self, pedido: IPedido) -> None:
        """Reacciona al cambio de estado del pedido."""
        pass


class MeseroObservador(IObservadorPedido):
    def __init__(self, servicio_push: ServicioPush):
        self.servicio_push = servicio_push

    def actualizar(self, pedido: IPedido) -> None:
        # Buscar el id del mesero que tomó el pedido o asignarlo (por simplicidad al id 1 o al que corresponda)
        # Según el contrato, el aviso debe incluir el número de mesa.
        mensaje = f"El pedido de la mesa {pedido.numero_mesa} está listo."
        # Nota: Aquí se necesita el id del mesero. En la Fase 5 se guarda en el pedido (id_mesero).
        # Como en el modelo puede no estar, usaremos un id genérico o lo sacamos del pedido si existe.
        id_mesero = getattr(pedido, "id_mesero", 1)  # Fallback al mesero 1 de ejemplo
        self.servicio_push.enviar_aviso(id_mesero, mensaje)


class DomiciliarioObservador(IObservadorPedido):
    def __init__(self, servicio_push: ServicioPush):
        self.servicio_push = servicio_push

    def actualizar(self, pedido: IPedido) -> None:
        # Asumiendo que el pedido a domicilio ya tiene asignado un id_domiciliario (Fase 6)
        id_domiciliario = getattr(pedido, "id_domiciliario", None)
        if id_domiciliario:
            mensaje = f"Tienes un nuevo pedido a domicilio listo para entregar (Pedido #{pedido.id_pedido})."
            self.servicio_push.enviar_aviso(id_domiciliario, mensaje)
