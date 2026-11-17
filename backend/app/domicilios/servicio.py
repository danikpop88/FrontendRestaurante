"""
servicio.py — El "GestorDomicilios", la capa de negocio del componente.

PAPEL EN LA ARQUITECTURA: contiene las reglas de negocio del componente.
Recibe las dependencias por constructor (repositorio, servicio de pago) para
cumplir con SOLID (Artículo 5).

Reglas clave que se aplican aquí:
- RN-08: Un pedido "En camino" no se reasigna a otro domiciliario.
- Asignación automática: al marcar listo un pedido a domicilio, se asigna al
  domiciliario con menos pedidos activos (D16, clarificación C9).
- Entrega: si es "Entregado", se registra el cobro por el Proxy de pago (RF-21).
  Si es "Devuelto", exige motivo y no genera cobro.
"""

from typing import List, Optional
from app.domicilios.repositorio import IRepositorioDomicilios
from app.domicilios.modelos import Domicilio
from app.ventas_pagos.servicio import IServicioPago
from app.compartido.excepciones import (
    ReglaNegocioError,
    NoEncontradoError,
    SinPermisoError,
)


class GestorDomicilios:
    def __init__(
        self, repositorio: IRepositorioDomicilios, servicio_pago: IServicioPago
    ):
        self.repositorio = repositorio
        self.servicio_pago = servicio_pago

    def asignar_automaticamente(self, domicilio: Domicilio) -> Domicilio:
        """
        Busca al domiciliario con menos pedidos activos y lo asigna (RF-24).
        Si no hay domiciliarios, el pedido queda pendiente (id_domiciliario = None).
        """
        id_domiciliario = self.repositorio.obtener_menos_pedidos_activos()

        if id_domiciliario:
            try:
                domicilio.asignar_domiciliario(id_domiciliario)
                self.repositorio.actualizar(domicilio)
            except ValueError as e:
                # Atrapamos el error de RN-08 si intentara reasignar un pedido En camino
                raise ReglaNegocioError(str(e))

        return domicilio

    def asignar_automaticamente_por_pedido(self, id_pedido: int) -> Domicilio:
        """Busca el domicilio de un pedido y le asigna un repartidor automáticamente."""
        domicilio = self.repositorio.obtener_por_pedido(id_pedido)
        if domicilio:
            return self.asignar_automaticamente(domicilio)
        return None

    def listar_mis_domicilios(self, id_domiciliario: int) -> List[Domicilio]:
        """Devuelve los domicilios asignados al domiciliario con los datos del cliente (RF-23)."""
        return self.repositorio.listar_por_domiciliario(id_domiciliario)

    def cerrar_entrega(
        self,
        id_domicilio: int,
        estado_entrega: str,
        motivo_devolucion: Optional[str],
        id_domiciliario: int,
    ) -> Domicilio:
        """
        El domiciliario marca el pedido como Entregado o Devuelto (RF-21).
        """
        domicilio = self.repositorio.obtener_por_id(id_domicilio)
        if not domicilio:
            raise NoEncontradoError("Domicilio no encontrado.")

        if domicilio.id_domiciliario != id_domiciliario:
            raise SinPermisoError("Este domicilio no está asignado a usted.")

        try:
            # actualizar_estado cambia el estado del Domicilio y del Pedido
            domicilio.actualizar_estado(estado_entrega, motivo_devolucion)
        except ValueError as e:
            raise ReglaNegocioError(str(e))

        # Si se entregó, se registra el cobro a través del Proxy (RF-21)
        if estado_entrega == "Entregado":
            self.servicio_pago.registrar_cobro(domicilio.pedido)

        self.repositorio.actualizar(domicilio)
        return domicilio
