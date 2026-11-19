"""
modelos.py — Clases de dominio y Patrón Command para la Cocina.
"""

from abc import ABC, abstractmethod

from app.autenticacion.modelos import IEmpleado
from app.pedidos.modelos import IPedido
from app.compartido.reloj import IReloj


class Chef(IEmpleado):
    """Empleado de cocina. Usa el constructor de IEmpleado."""

    def obtener_rol(self) -> str:
        return "Chef"


class IComandoCocina(ABC):
    @abstractmethod
    def ejecutar(self) -> None:
        pass


class ComandoMarcarListo(IComandoCocina):
    def __init__(self, pedido: IPedido, ejecutado_por: int, reloj: IReloj):
        self.pedido = pedido
        self.ejecutado_por = ejecutado_por
        self.reloj = reloj
        self.fecha_hora = reloj.ahora()

    def ejecutar(self) -> None:
        # Avanza el pedido de EnCocina a EnCamino
        self.pedido.siguiente()


class ComandoCancelarPedido(IComandoCocina):
    def __init__(self, pedido: IPedido, ejecutado_por: int, reloj: IReloj):
        self.pedido = pedido
        self.ejecutado_por = ejecutado_por
        self.reloj = reloj
        self.fecha_hora = reloj.ahora()

    def ejecutar(self) -> None:
        # El pedido valida si se puede cancelar (RN-01 / RN-04).
        # Se pasa el reloj inyectado, no None, para que la regla de los 5
        # minutos funcione igual que en el resto del sistema (D13).
        self.pedido.cancelar(self.reloj)