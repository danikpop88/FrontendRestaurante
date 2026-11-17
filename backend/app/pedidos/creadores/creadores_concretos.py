"""
creadores_concretos.py — Los dos creadores de pedidos (patrón FACTORY METHOD).

PAPEL EN LA ARQUITECTURA: cada clase construye un tipo de pedido y aplica las
reglas de creación de ese tipo (Artículo 3):

    CreadorPedidoMesa       -> PedidoMesa. La mesa debe existir.
    CreadorPedidoDomicilio  -> PedidoDomicilio. Exige dirección y pago contra
                               entrega (422) y, por RN-07, que el cliente tenga
                               un teléfono de contacto registrado (409).

Los creadores no tienen SQL (Artículo 2). Reciben funciones que main.py arma con
el repositorio de pedidos:

    existe_mesa(numero_mesa) -> bool
    obtener_telefono_cliente(id_cliente) -> str | None

La hora de creación sale del IReloj, no de datetime.now() (Plan §5.4).
"""

from typing import Callable

from app.compartido.excepciones import ReglaNegocioError, ValidacionError
from app.compartido.reloj import IReloj
from app.pedidos.creadores.creador_pedidos import (
    METODO_PAGO_CONTRA_ENTREGA,
    DatosPedido,
    ICreadorPedidos,
)
from app.pedidos.modelos import IPedido, PedidoDomicilio, PedidoMesa


class CreadorPedidoMesa(ICreadorPedidos):
    """Crea la orden que el mesero toma en una mesa."""

    def __init__(self, existe_mesa: Callable[[int], bool], reloj: IReloj):
        self._existe_mesa = existe_mesa
        self._reloj = reloj

    def crear_pedido(self, datos: DatosPedido) -> IPedido:
        if datos.numero_mesa is None:
            raise ValidacionError("El número de mesa es obligatorio.")
        if not self._existe_mesa(datos.numero_mesa):
            raise ValidacionError("La mesa indicada no existe.")
        return PedidoMesa(None, self._reloj.ahora(), datos.numero_mesa, detalle=datos.detalle)


class CreadorPedidoDomicilio(ICreadorPedidos):
    """Crea el pedido a domicilio del cliente (RF-06, RF-07 y RN-07)."""

    def __init__(self, obtener_telefono_cliente: Callable[[int], str | None], reloj: IReloj):
        self._obtener_telefono_cliente = obtener_telefono_cliente
        self._reloj = reloj

    def crear_pedido(self, datos: DatosPedido) -> IPedido:
        # 1. La forma de los datos (422): se reportan todos los motivos juntos.
        errores: list[str] = []
        if datos.direccion is None or not datos.direccion.strip():
            errores.append("La dirección de entrega es obligatoria.")
        if datos.metodo_pago != METODO_PAGO_CONTRA_ENTREGA:
            errores.append("El método de pago es obligatorio y debe ser CONTRA_ENTREGA.")
        if datos.id_cliente is None:
            errores.append("El pedido a domicilio necesita un cliente.")
        if errores:
            raise ValidacionError(errores)

        # 2. RN-07: no se acepta un pedido a domicilio sin teléfono de contacto (409).
        telefono = self._obtener_telefono_cliente(datos.id_cliente)
        if telefono is None or not telefono.strip():
            raise ReglaNegocioError(
                "No se puede hacer un pedido a domicilio sin un número de contacto."
            )

        return PedidoDomicilio(None, self._reloj.ahora(), datos.id_cliente,
                               datos.direccion.strip(), detalle=datos.detalle)