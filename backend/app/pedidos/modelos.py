"""
modelos.py — Las clases de dominio del componente "Pedidos" (nivel 4 del C4).

PAPEL EN LA ARQUITECTURA: guardan los datos del pedido y delegan en su estado
todo lo que cambia según la etapa (patrón State). No contienen SQL (eso es del
repositorio) ni deciden reglas por su cuenta: RN-01 y RN-04 las aplican los
estados (Artículo 3).

    TipoPedido        -> enumeración: EN_RESTAURANTE o DOMICILIO
    DetallePedido     -> una línea del pedido (producto, cantidad, precio)
    IPedido (ABC)     -> lo común: detalle, total con IVA, estado y observadores
      ├── PedidoMesa      (exige numero_mesa)
      └── PedidoDomicilio (exige id_cliente y direccion)

Convenciones (Artículo 11): los métodos del diagrama van en snake_case
(agregarProducto -> agregar_producto, calcularTotal -> calcular_total, ...).
El dinero es Decimal, porque PostgreSQL entrega NUMERIC como Decimal.

Observer: IPedido es el sujeto. Guarda una lista de observadores y, cuando el
chef marca el pedido como listo, el gestor llama a notificar_observadores().
La interfaz IObservadorPedido y los observadores concretos son de la Fase 7
(notificaciones/): aquí solo se espera que cada observador tenga actualizar(pedido).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from app.compartido.excepciones import ValidacionError
from app.compartido.reloj import IReloj
from app.pedidos.estados.estado_pedido import IEstadoPedido
from app.pedidos.estados.estados_concretos import EstadoRecibido


class TipoPedido(str, Enum):
    """Los dos tipos de pedido; el valor es el texto que se guarda en pedido.tipo_pedido."""
    EN_RESTAURANTE = "EN_RESTAURANTE"
    DOMICILIO = "DOMICILIO"


class DetallePedido:
    """Una línea del pedido: cuántas unidades de un producto, a qué precio."""

    def __init__(self, id_producto: int, nombre: str, cantidad: int,
                 precio_unitario: Decimal, observaciones_especiales: str | None = None):
        self.id_producto = id_producto
        self.nombre = nombre                          # nombre del producto, para mostrarlo
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario        # el precio al momento de pedir
        self.observaciones_especiales = observaciones_especiales

    def calcular_subtotal(self) -> Decimal:
        """DetallePedido.calcularSubtotal(): cantidad por precio unitario (atributo derivado)."""
        return self.cantidad * self.precio_unitario


class IPedido(ABC):
    """Lo común a los pedidos de mesa y a domicilio."""

    IVA = Decimal("0.19")     # constante de la clase; no se guarda en la base

    def __init__(self, id_pedido: int | None, fecha: datetime, id_cliente: int | None = None,
                 estado: IEstadoPedido | None = None,
                 detalle: list[DetallePedido] | None = None, id_chef: int | None = None):
        self.id_pedido = id_pedido            # None mientras el pedido aún no se guarda
        self.fecha = fecha                    # hora exacta de creación: RN-01 mide minutos
        self.id_cliente = id_cliente          # None en los pedidos de mesa
        self.id_chef = id_chef                # se llena cuando el chef toma el pedido
        self.detalle: list[DetallePedido] = list(detalle) if detalle else []
        self._estado: IEstadoPedido = estado if estado is not None else EstadoRecibido()
        self._observadores: list = []         # IObservadorPedido (Fase 7)

    # ----------------------------------------------------------- tipo
    @abstractmethod
    def obtener_tipo(self) -> TipoPedido:
        """Devuelve si es un pedido de mesa o a domicilio."""

    # ----------------------------------------------------------- detalle
    def agregar_producto(self, detalle: DetallePedido) -> None:
        """
        Pedido.agregarProducto(): agrega una línea. Si el producto ya está en el
        pedido, suma las cantidades (la llave de detalle_pedido no admite duplicados).
        """
        if detalle.cantidad < 1:
            raise ValidacionError("La cantidad debe ser al menos 1.")
        for existente in self.detalle:
            if existente.id_producto == detalle.id_producto:
                existente.cantidad += detalle.cantidad
                if detalle.observaciones_especiales is not None:
                    existente.observaciones_especiales = detalle.observaciones_especiales
                return
        self.detalle.append(detalle)

    def eliminar_producto(self, id_producto: int) -> None:
        """Pedido.eliminarProducto(): quita la línea de ese producto (si no está, no hace nada)."""
        self.detalle = [d for d in self.detalle if d.id_producto != id_producto]

    def reemplazar_detalle(self, nuevo_detalle: list[DetallePedido]) -> None:
        """Cambia todas las líneas por una lista nueva (modificar una orden: PUT con la lista completa)."""
        self.detalle = []
        for detalle in nuevo_detalle:
            self.agregar_producto(detalle)

    def calcular_total(self) -> Decimal:
        """Pedido.calcularTotal(): suma de subtotales más el IVA del 19 %, a 2 decimales."""
        subtotal = sum((d.calcular_subtotal() for d in self.detalle), Decimal("0"))
        return (subtotal * (1 + self.IVA)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def total(self) -> Decimal:
        """El atributo derivado /total del diagrama. El Proxy de pago lo lee de aquí."""
        return self.calcular_total()

    # ----------------------------------------------------------- State
    def obtener_estado(self) -> str:
        """Pedido.obtenerEstado(): el nombre del estado actual (Recibido, EnCocina...)."""
        return self._estado.obtener_estado()

    def set_estado_pedido(self, estado: IEstadoPedido) -> None:
        """Pedido.setEstadoPedido(): lo usan los estados al pasar al siguiente."""
        self._estado = estado

    def modificar(self, reloj: IReloj) -> None:
        """Pregunta al estado si se puede modificar (RN-01 y RN-04); si no, lanza ReglaNegocioError."""
        self._estado.modificar(self, reloj)

    def cancelar(self, reloj: IReloj) -> bool:
        """Pedido.cancelar(): True si el estado lo permite; si no, ReglaNegocioError. No borra nada."""
        return self._estado.cancelar(self, reloj)

    def siguiente(self) -> None:
        """Pasa el pedido al estado siguiente (lo decide el estado actual)."""
        self._estado.siguiente(self)

    # ----------------------------------------------------------- Observer
    def agregar_observador(self, observador) -> None:
        """Registra a quien debe enterarse cuando el pedido esté listo."""
        self._observadores.append(observador)

    def quitar_observador(self, observador) -> None:
        if observador in self._observadores:
            self._observadores.remove(observador)

    def notificar_observadores(self) -> None:
        """Pedido.notificarObservadores(): avisa a cada observador llamando a actualizar(pedido)."""
        for observador in list(self._observadores):
            observador.actualizar(self)

    # ----------------------------------------------------------- validez
    def es_valido(self) -> bool:
        """
        Pedido.esValido(): lo consulta el Proxy de pago antes de delegar. Un pedido
        es válido si tiene al menos una línea y todas las cantidades son >= 1.
        """
        return bool(self.detalle) and all(d.cantidad >= 1 for d in self.detalle)


class PedidoMesa(IPedido):
    """Orden que el mesero toma en una mesa del restaurante."""

    def __init__(self, id_pedido: int | None, fecha: datetime, numero_mesa: int,
                 estado: IEstadoPedido | None = None,
                 detalle: list[DetallePedido] | None = None, id_chef: int | None = None):
        super().__init__(id_pedido, fecha, None, estado, detalle, id_chef)
        self.numero_mesa = numero_mesa

    def obtener_tipo(self) -> TipoPedido:
        return TipoPedido.EN_RESTAURANTE

    def es_valido(self) -> bool:
        return super().es_valido() and self.numero_mesa is not None


class PedidoDomicilio(IPedido):
    """Pedido que el cliente hace desde la aplicación para recibir en su dirección."""

    def __init__(self, id_pedido: int | None, fecha: datetime, id_cliente: int,
                 direccion: str, estado: IEstadoPedido | None = None,
                 detalle: list[DetallePedido] | None = None, id_chef: int | None = None):
        super().__init__(id_pedido, fecha, id_cliente, estado, detalle, id_chef)
        self.direccion = direccion

    def obtener_tipo(self) -> TipoPedido:
        return TipoPedido.DOMICILIO

    def es_valido(self) -> bool:
        return (super().es_valido() and self.id_cliente is not None
                and bool(self.direccion and self.direccion.strip()))