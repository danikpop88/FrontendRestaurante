"""
creador_pedidos.py — La interfaz del patrón FACTORY METHOD de los pedidos.

PAPEL EN LA ARQUITECTURA: ICreadorPedidos es la clase abstracta (ABC) de la que
depende GestorPedidos (Artículo 5). El gestor no usa new ni if para elegir qué
pedido construir: recibe un mapa TipoPedido -> creador y llama crear_pedido().
Cada creador concreto sabe construir UN tipo de pedido y aplica las reglas de
creación propias de ese tipo (Artículo 4, Plan §5.2).

DatosPedido es lo que el gestor le entrega al creador: el detalle ya resuelto
(productos con su precio y disponibilidad verificada, RN-05) y los datos propios
de cada tipo. Los campos que no aplican a un tipo se ignoran.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.pedidos.modelos import DetallePedido, IPedido

METODO_PAGO_CONTRA_ENTREGA = "CONTRA_ENTREGA"     # RF-07: el único método del MVP


@dataclass
class DatosPedido:
    """Los datos con los que se crea un pedido."""
    detalle: list[DetallePedido] = field(default_factory=list)
    id_cliente: int | None = None          # quién hace el pedido a domicilio
    direccion: str | None = None           # solo DOMICILIO
    metodo_pago: str | None = None         # solo DOMICILIO
    numero_mesa: int | None = None         # solo EN_RESTAURANTE


class ICreadorPedidos(ABC):
    """Contrato de un creador: sabe construir un tipo de pedido."""

    @abstractmethod
    def crear_pedido(self, datos: DatosPedido) -> IPedido:
        """
        Valida los datos propios del tipo y devuelve el pedido nuevo, en estado
        Recibido y con la hora actual como fecha. Lanza ValidacionError (422) si
        los datos no tienen la forma correcta, o ReglaNegocioError (409) si se
        viola una regla de negocio. No guarda nada: eso es del repositorio.
        """