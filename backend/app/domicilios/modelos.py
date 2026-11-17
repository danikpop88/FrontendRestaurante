# backend/app/domicilios/modelos.py
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from app.pedidos.modelos import IPedido, PedidoDomicilio


class Domicilio:
    def __init__(
        self,
        id_domicilio: Optional[int],
        pedido: PedidoDomicilio,
        id_domiciliario: Optional[int],
        direccion: str,
        estado_entrega: Optional[str] = None,
        fecha_entrega: Optional[date] = None,
        motivo_devolucion: Optional[str] = None,
    ):
        self.id_domicilio = id_domicilio
        self.pedido = pedido
        self.id_domiciliario = id_domiciliario
        self.direccion = direccion
        self.estado_entrega = estado_entrega  # "Entregado", "Devuelto" o None
        self.fecha_entrega = fecha_entrega
        self.motivo_devolucion = motivo_devolucion

    def asignarDomiciliario(self, id_domiciliario: int):
        """
        Asigna el domiciliario. RN-08: Un pedido 'En camino' no se reasigna.
        """
        if (
            self.pedido.obtenerEstado() == "EnCamino"
            and self.id_domiciliario is not None
        ):
            raise ValueError("No se puede reasignar un pedido que ya está En camino.")
        self.id_domiciliario = id_domiciliario

    def actualizarEstado(self, nuevo_estado: str, motivo: Optional[str] = None):
        """
        Cierra la entrega.
        """
        if nuevo_estado not in ("Entregado", "Devuelto"):
            raise ValueError("Estado de entrega inválido.")

        if self.estado_entrega is not None:
            raise ValueError("La entrega ya fue cerrada.")

        if nuevo_estado == "Devuelto":
            if not motivo:
                raise ValueError("El motivo de devolución es obligatorio.")
            self.motivo_devolucion = motivo
        else:
            self.pedido.siguiente()  # Pasa de EnCamino a Entregado

        self.estado_entrega = nuevo_estado
        self.fecha_entrega = date.today()
