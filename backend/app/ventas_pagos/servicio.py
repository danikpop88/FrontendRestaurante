"""
servicio.py — ServicioPago: el patrón PROXY del componente "Ventas y pagos".

PAPEL EN LA ARQUITECTURA: GestorPedidos (y más adelante GestorDomicilios) depende
de la abstracta IServicioPago, nunca de una clase concreta (Artículo 5). Detrás
hay dos implementaciones:

    IServicioPago      -> contrato (ABC)
    ServicioPagoReal   -> el que de verdad guarda y confirma el Pago
    ServicioPagoProxy  -> se pone DELANTE del real: controla el acceso. Valida el
                          pedido con es_valido(), registra la transacción y
                          recién entonces delega.

En el MVP el cobro es contra entrega y se SIMULA (no hay pasarela de pago): el
"servicio real" solo cambia el estado del Pago en la base.

Reglas (Artículo 3): un pedido inválido nunca llega al servicio real
(ReglaNegocioError -> 409); un pago ya cobrado no se cobra dos veces (409);
cobrar un pedido sin pago es NoEncontradoError (404).

Del pedido solo se usan: id_pedido, id_cliente, total y es_valido().
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime

from app.compartido.excepciones import NoEncontradoError, ReglaNegocioError
from app.compartido.reloj import IReloj
from app.ventas_pagos.modelos import Pago
from app.ventas_pagos.repositorio import IRepositorioPagos

registro = logging.getLogger("mesa_abuela.pagos")


class IServicioPago(ABC):
    """Contrato del servicio de pago."""

    @abstractmethod
    def registrar_pago(self, pedido) -> Pago:
        """Crea el pago del pedido en estado 'Pendiente de Cobro' (RF-07)."""

    @abstractmethod
    def registrar_cobro(self, pedido) -> Pago:
        """Pasa el pago del pedido a 'Cobrado' (RF-21)."""


class ServicioPagoReal(IServicioPago):
    """El servicio que ejecuta el pago (simulado: solo guarda y confirma)."""

    def __init__(self, repositorio: IRepositorioPagos, reloj: IReloj):
        self._repositorio = repositorio
        self._reloj = reloj

    def registrar_pago(self, pedido) -> Pago:
        pago = Pago(None, pedido.id_pedido, pedido.id_cliente, pedido.total,
                    self._reloj.ahora().date())
        return self._repositorio.guardar(pago)

    def registrar_cobro(self, pedido) -> Pago:
        pago = self._repositorio.obtener_por_pedido(pedido.id_pedido)
        if pago is None:
            raise NoEncontradoError("El pedido no tiene un pago registrado.")
        if pago.esta_cobrado():
            raise ReglaNegocioError("El pago de este pedido ya fue cobrado.")
        pago.confirmar_pago(self._reloj.ahora().date())
        self._repositorio.actualizar(pago)
        return pago


class ServicioPagoProxy(IServicioPago):
    """Controla el acceso al servicio real: valida, registra la transacción y delega."""

    def __init__(self, servicio_real: IServicioPago, reloj: IReloj):
        self._real = servicio_real
        self._reloj = reloj
        self.transacciones: list[tuple[datetime, str, int]] = []   # (cuándo, operación, id_pedido)

    def registrar_pago(self, pedido) -> Pago:
        self._validar(pedido)
        self._registrar_transaccion("registrar_pago", pedido)
        return self._real.registrar_pago(pedido)

    def registrar_cobro(self, pedido) -> Pago:
        self._validar(pedido)
        self._registrar_transaccion("registrar_cobro", pedido)
        return self._real.registrar_cobro(pedido)

    def _validar(self, pedido) -> None:
        if not pedido.es_valido():
            raise ReglaNegocioError("El pedido no es válido para registrar el pago.")

    def _registrar_transaccion(self, operacion: str, pedido) -> None:
        self.transacciones.append((self._reloj.ahora(), operacion, pedido.id_pedido))
        registro.info("Transacción de pago: %s del pedido %s", operacion, pedido.id_pedido)