"""
estados_concretos.py — Los cuatro estados del pedido (patrón STATE, nivel 4 del C4).

PAPEL EN LA ARQUITECTURA: cada clase encapsula el comportamiento de una etapa
del pedido y sabe a cuál pasa (decisión D12 de 4_research.md: la transición vive
dentro de cada estado).

    EstadoRecibido  -> EstadoEnCocina  (el chef toma el pedido)
    EstadoEnCocina  -> EstadoEnCamino  (el chef lo marca listo)
    EstadoEnCamino  -> EstadoEntregado (se cierra la entrega y se cobra)
    EstadoEntregado -> (final)

Reglas de negocio que aplican (Artículo 3):
  - RN-01: en Recibido solo se modifica o cancela si pasaron MENOS de 5 minutos
    desde pedido.fecha. Con 5 minutos o más se rechaza.
  - RN-04: en EnCocina (y en los estados siguientes) no se modifica ni se cancela.

Todos los rechazos son ReglaNegocioError, que main.py traduce a 409 con el
mensaje en español.

estado_desde_nombre() lo usa el repositorio para reconstruir el estado a partir
del texto guardado en la base.
"""

from datetime import timedelta

from app.compartido.excepciones import ReglaNegocioError
from app.compartido.reloj import IReloj
from app.pedidos.estados.estado_pedido import IEstadoPedido

MINUTOS_PLAZO_PEDIDO = 5      # RN-01: ventana para modificar o cancelar


def _exigir_plazo(pedido, reloj: IReloj, mensaje: str) -> None:
    """RN-01: lanza ReglaNegocioError si pasaron 5 minutos o más desde la creación."""
    transcurrido = reloj.ahora() - pedido.fecha
    if transcurrido >= timedelta(minutes=MINUTOS_PLAZO_PEDIDO):
        raise ReglaNegocioError(mensaje)


class EstadoRecibido(IEstadoPedido):
    """El pedido se registró. Se puede modificar o cancelar durante 5 minutos (RN-01)."""

    def modificar(self, pedido, reloj: IReloj) -> None:
        _exigir_plazo(pedido, reloj,
                      "La orden ya no se puede modificar: pasaron más de 5 minutos.")

    def cancelar(self, pedido, reloj: IReloj) -> bool:
        _exigir_plazo(pedido, reloj,
                      "El pedido ya no se puede cancelar: pasaron más de 5 minutos.")
        return True

    def siguiente(self, pedido) -> None:
        pedido.set_estado_pedido(EstadoEnCocina())

    def obtener_estado(self) -> str:
        return "Recibido"


class EstadoEnCocina(IEstadoPedido):
    """El chef lo tomó y se está preparando. No se modifica ni se cancela (RN-04)."""

    def modificar(self, pedido, reloj: IReloj) -> None:
        raise ReglaNegocioError("La orden ya está en cocina y no se puede modificar.")

    def cancelar(self, pedido, reloj: IReloj) -> bool:
        raise ReglaNegocioError("El pedido ya está en cocina y no se puede cancelar.")

    def siguiente(self, pedido) -> None:
        pedido.set_estado_pedido(EstadoEnCamino())

    def obtener_estado(self) -> str:
        return "EnCocina"


class EstadoEnCamino(IEstadoPedido):
    """Salió de cocina (al domiciliario o a la mesa). Ya no se modifica ni se cancela."""

    def modificar(self, pedido, reloj: IReloj) -> None:
        raise ReglaNegocioError("La orden ya salió de cocina y no se puede modificar.")

    def cancelar(self, pedido, reloj: IReloj) -> bool:
        raise ReglaNegocioError("El pedido ya salió de cocina y no se puede cancelar.")

    def siguiente(self, pedido) -> None:
        pedido.set_estado_pedido(EstadoEntregado())

    def obtener_estado(self) -> str:
        return "EnCamino"


class EstadoEntregado(IEstadoPedido):
    """Pedido entregado y cobrado. Estado final."""

    def modificar(self, pedido, reloj: IReloj) -> None:
        raise ReglaNegocioError("El pedido ya fue entregado y no se puede modificar.")

    def cancelar(self, pedido, reloj: IReloj) -> bool:
        raise ReglaNegocioError("El pedido ya fue entregado y no se puede cancelar.")

    def siguiente(self, pedido) -> None:
        raise ReglaNegocioError("El pedido ya fue entregado: no tiene un estado siguiente.")

    def obtener_estado(self) -> str:
        return "Entregado"


_ESTADOS = {
    "Recibido": EstadoRecibido,
    "EnCocina": EstadoEnCocina,
    "EnCamino": EstadoEnCamino,
    "Entregado": EstadoEntregado,
}


def estado_desde_nombre(nombre: str) -> IEstadoPedido:
    """Crea el estado que corresponde al texto guardado en pedido.estado_pedido."""
    clase = _ESTADOS.get(nombre)
    if clase is None:
        raise ValueError(f"Estado de pedido desconocido: {nombre}")
    return clase()