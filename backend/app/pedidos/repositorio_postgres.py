"""
repositorio_postgres.py — Implementación de IRepositorioPedidos con psycopg 3.

PAPEL EN LA ARQUITECTURA: es la ÚNICA pieza del módulo pedidos/ que escribe SQL
(Artículo 2). Todos los valores viajan como parámetros (%s con tupla), nunca
concatenados (Artículo 6). Los fragmentos de WHERE que se arman son literales
fijos escritos aquí; ningún dato del usuario entra en el texto SQL.

Transacciones (Plan §5.9): crear un pedido con su detalle, su domicilio y su pago
pendiente es UNA transacción; cancelar (eliminar) borra todo en UNA transacción;
actualizar (estado, chef, total, mesa y detalle) también. Si algo falla antes del
commit se hace rollback.

Las filas se convierten en clases de dominio: el estado se reconstruye con
estado_desde_nombre(), y el total NO se lee de la base porque IPedido lo calcula
del detalle (el valor guardado es el mismo, con el IVA del 19 %).
"""

from app.pedidos.estados.estados_concretos import estado_desde_nombre
from app.pedidos.modelos import DetallePedido, IPedido, PedidoDomicilio, PedidoMesa, TipoPedido
from app.pedidos.repositorio import IRepositorioPedidos
from app.ventas_pagos.modelos import PENDIENTE_DE_COBRO

# Un pedido con la dirección de su domicilio (NULL en los pedidos de mesa).
_SELECT_PEDIDO = (
    "SELECT p.id_pedido, p.tipo_pedido, p.estado_pedido, p.fecha, p.id_cliente, "
    "p.numero_mesa, p.id_chef, d.direccion "
    "FROM pedido p LEFT JOIN domicilio d ON d.id_pedido = p.id_pedido"
)
_ORDEN = " ORDER BY p.fecha DESC, p.id_pedido DESC"


class RepositorioPedidosPostgres(IRepositorioPedidos):

    def __init__(self, conexion):
        self._conexion = conexion

    # ----------------------------------------------------------- escrituras
    def crear(self, pedido: IPedido) -> IPedido:
        try:
            with self._conexion.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO pedido (tipo_pedido, estado_pedido, fecha, total, "
                    "id_cliente, numero_mesa, id_chef) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_pedido",
                    (pedido.obtener_tipo().value, pedido.obtener_estado(), pedido.fecha,
                     pedido.total, pedido.id_cliente, getattr(pedido, "numero_mesa", None),
                     pedido.id_chef),
                )
                pedido.id_pedido = cursor.fetchone()[0]
                self._insertar_detalle(cursor, pedido)
                if isinstance(pedido, PedidoDomicilio):
                    # id_domiciliario queda NULL: el pedido está pendiente de asignar.
                    cursor.execute(
                        "INSERT INTO domicilio (id_pedido, direccion) VALUES (%s, %s)",
                        (pedido.id_pedido, pedido.direccion),
                    )
                    cursor.execute(
                        "INSERT INTO pago (id_pedido, id_cliente, estado_pago, fecha, monto) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (pedido.id_pedido, pedido.id_cliente, PENDIENTE_DE_COBRO,
                         pedido.fecha.date(), pedido.total),
                    )
            self._conexion.commit()
        except Exception:
            self._conexion.rollback()
            pedido.id_pedido = None
            raise
        return pedido

    def actualizar(self, pedido: IPedido) -> None:
        # Guarda lo que puede cambiar en un pedido ya creado: el estado y el chef
        # (Cocina: tomar y marcar listo), y el total, la mesa y el detalle
        # (el mesero modifica la orden).
        try:
            with self._conexion.cursor() as cursor:
                cursor.execute(
                    "UPDATE pedido SET estado_pedido = %s, id_chef = %s, total = %s, "
                    "numero_mesa = %s WHERE id_pedido = %s",
                    (pedido.obtener_estado(), pedido.id_chef, pedido.total,
                     getattr(pedido, "numero_mesa", None), pedido.id_pedido),
                )
                cursor.execute(
                    "DELETE FROM detalle_pedido WHERE id_pedido = %s", (pedido.id_pedido,)
                )
                self._insertar_detalle(cursor, pedido)
            self._conexion.commit()
        except Exception:
            self._conexion.rollback()
            raise

    def eliminar(self, id_pedido: int) -> None:
        # Primero las tablas que apuntan al pedido, al final el pedido (llaves foráneas).
        try:
            with self._conexion.cursor() as cursor:
                cursor.execute("DELETE FROM detalle_pedido WHERE id_pedido = %s", (id_pedido,))
                cursor.execute("DELETE FROM domicilio WHERE id_pedido = %s", (id_pedido,))
                cursor.execute("DELETE FROM pago WHERE id_pedido = %s", (id_pedido,))
                cursor.execute("DELETE FROM pedido WHERE id_pedido = %s", (id_pedido,))
            self._conexion.commit()
        except Exception:
            self._conexion.rollback()
            raise

    # ----------------------------------------------------------- consultas
    def obtener_por_id(self, id_pedido: int) -> IPedido | None:
        pedidos = self._consultar(["p.id_pedido = %s"], (id_pedido,))
        return pedidos[0] if pedidos else None

    def listar_de_cliente(self, id_cliente: int, estado_pedido: str | None = None) -> list[IPedido]:
        condiciones = ["p.id_cliente = %s"]
        parametros: list = [id_cliente]
        if estado_pedido is not None:
            condiciones.append("p.estado_pedido = %s")
            parametros.append(estado_pedido)
        return self._consultar(condiciones, tuple(parametros))

    def listar_de_mesa(self, estado_pedido: str | None = None) -> list[IPedido]:
        condiciones = ["p.tipo_pedido = %s"]
        parametros: list = [TipoPedido.EN_RESTAURANTE.value]
        if estado_pedido is not None:
            condiciones.append("p.estado_pedido = %s")
            parametros.append(estado_pedido)
        return self._consultar(condiciones, tuple(parametros))

    def obtener_telefono_cliente(self, id_cliente: int) -> str | None:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                "SELECT telefono FROM usuario WHERE id_usuario = %s", (id_cliente,)
            )
            fila = cursor.fetchone()
        return fila[0] if fila else None

    def existe_mesa(self, numero_mesa: int) -> bool:
        with self._conexion.cursor() as cursor:
            cursor.execute("SELECT 1 FROM mesa WHERE numero_mesa = %s", (numero_mesa,))
            return cursor.fetchone() is not None

    # ----------------------------------------------------------- internos
    def _insertar_detalle(self, cursor, pedido: IPedido) -> None:
        cursor.executemany(
            "INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, "
            "precio_unitario, observaciones_especiales) VALUES (%s, %s, %s, %s, %s)",
            [(pedido.id_pedido, d.id_producto, d.cantidad, d.precio_unitario,
              d.observaciones_especiales) for d in pedido.detalle],
        )

    def _consultar(self, condiciones: list[str], parametros: tuple) -> list[IPedido]:
        """Lee los pedidos que cumplen las condiciones, con su detalle (2 consultas en total)."""
        sql = _SELECT_PEDIDO
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        sql += _ORDEN
        with self._conexion.cursor() as cursor:
            cursor.execute(sql, parametros)
            filas = cursor.fetchall()
        detalles = self._leer_detalles([fila[0] for fila in filas])
        return [self._a_dominio(fila, detalles.get(fila[0], [])) for fila in filas]

    def _leer_detalles(self, ids_pedido: list[int]) -> dict[int, list[DetallePedido]]:
        """Trae las líneas de varios pedidos de una sola vez: id_pedido -> sus líneas."""
        if not ids_pedido:
            return {}
        with self._conexion.cursor() as cursor:
            cursor.execute(
                "SELECT dp.id_pedido, dp.id_producto, pr.nombre, dp.cantidad, "
                "dp.precio_unitario, dp.observaciones_especiales "
                "FROM detalle_pedido dp JOIN producto pr ON pr.id_producto = dp.id_producto "
                "WHERE dp.id_pedido = ANY(%s) ORDER BY dp.id_pedido, dp.id_producto",
                (ids_pedido,),
            )
            filas = cursor.fetchall()
        detalles: dict[int, list[DetallePedido]] = {}
        for id_pedido, id_producto, nombre, cantidad, precio, observaciones in filas:
            detalles.setdefault(id_pedido, []).append(
                DetallePedido(id_producto, nombre, cantidad, precio, observaciones)
            )
        return detalles

    def _a_dominio(self, fila: tuple, detalle: list[DetallePedido]) -> IPedido:
        """Convierte una fila en PedidoMesa o PedidoDomicilio, con su estado reconstruido."""
        id_pedido, tipo, estado, fecha, id_cliente, numero_mesa, id_chef, direccion = fila
        estado_pedido = estado_desde_nombre(estado)
        if tipo == TipoPedido.DOMICILIO.value:
            return PedidoDomicilio(id_pedido, fecha, id_cliente, direccion or "",
                                   estado_pedido, detalle, id_chef)
        return PedidoMesa(id_pedido, fecha, numero_mesa, estado_pedido, detalle, id_chef)