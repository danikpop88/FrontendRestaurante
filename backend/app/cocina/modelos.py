"""
modelos.py — Clases de dominio y Patrón Command para la Cocina.

PAPEL EN LA ARQUITECTURA: define al Chef (que extiende de IEmpleado) y los
comandos (ComandoMarcarListo, ComandoCancelarPedido). El patrón Command permite
encapsular las acciones de cocina como objetos, guardando quién las ejecutó y
cuándo, para tener trazabilidad.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from app.autenticacion.modelos import IEmpleado
from app.pedidos.modelos import IPedido
from app.compartido.reloj import IReloj


class Chef(IEmpleado):
    def __init__(self, id_empleado: int, nombre: str, email: str, contrasena: str):
        super().__init__(id_empleado, nombre, email, contrasena, "Chef", True)


class IComandoCocina(ABC):
    @abstractmethod
    def ejecutar(self) -> None:
        pass


class ComandoMarcarListo(IComandoCocina):
    def __init__(self, pedido: IPedido, ejecutado_por: int, reloj: IReloj):
        self.pedido = pedido
        self.ejecutado_por = ejecutado_por
        self.fecha_hora = reloj.ahora()

    def ejecutar(self) -> None:
        # Avanza el pedido de EnCocina a EnCamino
        self.pedido.siguiente()


class ComandoCancelarPedido(IComandoCocina):
    def __init__(self, pedido: IPedido, ejecutado_por: int, reloj: IReloj):
        self.pedido = pedido
        self.ejecutado_por = ejecutado_por
        self.fecha_hora = reloj.ahora()

    def ejecutar(self) -> None:
        # Cancela el pedido (validará si se puede)
        self.pedido.cancelar(reloj=None)  # El pedido maneja su propia regla
