"""
estado_pedido.py — La interfaz del patrón STATE del ciclo de vida del pedido.

PAPEL EN LA ARQUITECTURA: IEstadoPedido es la clase abstracta (ABC) de la que
dependen IPedido y los gestores (Artículo 5). Cada estado concreto decide qué
acciones permite y a qué estado puede pasar, así el pedido no necesita cadenas
de if por estado (Artículo 4). Las reglas RN-01 y RN-04 viven en los estados
(Artículo 3, Plan §5.3).

El IReloj se recibe por parámetro: los estados nunca llaman a datetime.now()
(Plan §5.4), y así el plazo de 5 minutos se prueba sin esperar.

El pedido se pasa sin tipo concreto (es un IPedido) para no crear un import
circular entre modelos.py y estados/.
"""

from abc import ABC, abstractmethod

from app.compartido.reloj import IReloj


class IEstadoPedido(ABC):
    """Contrato de un estado del pedido."""

    @abstractmethod
    def modificar(self, pedido, reloj: IReloj) -> None:
        """Comprueba que el pedido se pueda modificar; si no, lanza ReglaNegocioError (409)."""

    @abstractmethod
    def cancelar(self, pedido, reloj: IReloj) -> bool:
        """
        Comprueba que el pedido se pueda cancelar. Devuelve True si se puede;
        si no, lanza ReglaNegocioError (409). El estado no borra nada: quien
        elimina el pedido es el repositorio, a pedido del gestor.
        """

    @abstractmethod
    def siguiente(self, pedido) -> None:
        """Pasa el pedido al estado que sigue; si no hay siguiente, lanza ReglaNegocioError."""

    @abstractmethod
    def obtener_estado(self) -> str:
        """Devuelve el nombre del estado, tal como se guarda en pedido.estado_pedido."""