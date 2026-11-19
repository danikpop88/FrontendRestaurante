"""
repositorio_postgres.py — La implementación real del repositorio con PostgreSQL.

PAPEL EN LA ARQUITECTURA: es la capa de datos del componente "Domicilios".
Usa psycopg con consultas parametrizadas (Artículo 2 y 6 de la constitución)
para evitar inyección SQL. Su trabajo es convertir las filas de la base de
datos a objetos de dominio (Domicilio) y viceversa.
"""

from typing import List, Optional

from app.domicilios.repositorio import IRepositorioDomicilios
from app.domicilios.modelos import Domicilio


# Columnas del SELECT completo (domicilio + pedido + cliente), en este orden.
_COLUMNAS = (
    "d.id_domicilio, d.id_pedido, d.id_domiciliario, d.direccion, "
    "d.estado_entrega, d.fecha_entrega, d.motivo_devolucion, "
    "p.estado_pedido, p.total, p.id_cliente, "
    "u.nombre AS cliente_nombre, u.telefono AS cliente_telefono"
)


class _ClienteRef:
    """Datos mínimos del cliente que la ruta de domicilios muestra."""

    def __init__(self, nombre: str, telefono: str):
        self.nombre = nombre
        self.telefono = telefono


class _PedidoRef:
    """
    Sustituto mínimo del PedidoDomicilio para que Domicilio, la ruta y el
    servicio de pago funcionen sin reconstruir el pedido completo (eso lo
    hace el repositorio de pedidos, no el de domicilios).
    """

    def __init__(self, id_pedido, id_cliente, estado_pedido, total,
                 nombre_cliente: str, telefono_cliente: str):
        self.id_pedido = id_pedido
        self.id_cliente = id_cliente
        self._estado = estado_pedido
        self.total = total
        self.cliente = _ClienteRef(nombre_cliente or "", telefono_cliente or "")

    # --- estado del pedido: dos alias, uno para el modelo y otro para la ruta
    def obtenerEstado(self) -> str:
        return self._estado

    def obtener_estado(self) -> str:
        return self._estado

    def siguiente(self) -> None:
        # Domicilio.actualizarEstado() llama siguiente() al cerrar la entrega.
        # El único cambio válido en este flujo es EnCamino -> Entregado.
        if self._estado == "EnCamino":
            self._estado = "Entregado"

    # --- validación que el Proxy de pago hace antes de cobrar
    def es_valido(self) -> bool:
        return self.total is not None and self.total > 0


class RepositorioDomiciliosPostgres(IRepositorioDomicilios):

    def __init__(self, conexion):
        self.conexion = conexion

    # ----------------------------------------------------------- conversión
    def _a_domicilio(self, fila) -> Domicilio:
        (id_domicilio, id_pedido, id_domiciliario, direccion,
         estado_entrega, fecha_entrega, motivo_devolucion,
         estado_pedido, total, id_cliente,
         cliente_nombre, cliente_telefono) = fila
        return Domicilio(
            id_domicilio=id_domicilio,
            pedido=_PedidoRef(
                id_pedido=id_pedido,
                id_cliente=id_cliente,
                estado_pedido=estado_pedido,
                total=total,
                nombre_cliente=cliente_nombre,
                telefono_cliente=cliente_telefono,
            ),
            id_domiciliario=id_domiciliario,
            direccion=direccion,
            estado_entrega=estado_entrega,
            fecha_entrega=fecha_entrega,
            motivo_devolucion=motivo_devolucion,
        )

    # ----------------------------------------------------------- consultas
    def obtener_menos_pedidos_activos(self) -> Optional[int]:
        sql = """
            SELECT u.id_usuario, COUNT(p.id_pedido) AS pedidos_activos
            FROM usuario u
            LEFT JOIN domicilio d ON u.id_usuario = d.id_domiciliario
            LEFT JOIN pedido p ON d.id_pedido = p.id_pedido AND p.estado_pedido = 'EnCamino'
            WHERE u.tipo_cargo = 'Domiciliario' AND u.estado = TRUE
            GROUP BY u.id_usuario
            ORDER BY pedidos_activos ASC
            LIMIT 1;
        """
        with self.conexion.cursor() as cur:
            cur.execute(sql)
            fila = cur.fetchone()
        return fila[0] if fila else None

    def obtener_por_id(self, id_domicilio: int) -> Optional[Domicilio]:
        sql = f"""
            SELECT {_COLUMNAS}
            FROM domicilio d
            JOIN pedido p ON p.id_pedido = d.id_pedido
            LEFT JOIN usuario u ON u.id_usuario = p.id_cliente
            WHERE d.id_domicilio = %s;
        """
        with self.conexion.cursor() as cur:
            cur.execute(sql, (id_domicilio,))
            fila = cur.fetchone()
        return self._a_domicilio(fila) if fila else None

    def obtener_por_pedido(self, id_pedido: int) -> Optional[Domicilio]:
        sql = f"""
            SELECT {_COLUMNAS}
            FROM domicilio d
            JOIN pedido p ON p.id_pedido = d.id_pedido
            LEFT JOIN usuario u ON u.id_usuario = p.id_cliente
            WHERE d.id_pedido = %s;
        """
        with self.conexion.cursor() as cur:
            cur.execute(sql, (id_pedido,))
            fila = cur.fetchone()
        return self._a_domicilio(fila) if fila else None

    def listar_por_domiciliario(self, id_domiciliario: int) -> List[Domicilio]:
        sql = f"""
            SELECT {_COLUMNAS}
            FROM domicilio d
            JOIN pedido p ON p.id_pedido = d.id_pedido
            LEFT JOIN usuario u ON u.id_usuario = p.id_cliente
            WHERE d.id_domiciliario = %s
            ORDER BY p.fecha DESC;
        """
        with self.conexion.cursor() as cur:
            cur.execute(sql, (id_domiciliario,))
            filas = cur.fetchall()
        return [self._a_domicilio(f) for f in filas]

    # ----------------------------------------------------------- escrituras
    def crear(self, domicilio: Domicilio) -> Domicilio:
        sql = """
            INSERT INTO domicilio (id_pedido, id_domiciliario, direccion,
                                   estado_entrega, fecha_entrega, motivo_devolucion)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_domicilio;
        """
        with self.conexion.cursor() as cur:
            cur.execute(
                sql,
                (
                    domicilio.pedido.id_pedido,
                    domicilio.id_domiciliario,
                    domicilio.direccion,
                    domicilio.estado_entrega,
                    domicilio.fecha_entrega,
                    domicilio.motivo_devolucion,
                ),
            )
            domicilio.id_domicilio = cur.fetchone()[0]
        self.conexion.commit()
        return domicilio

    def actualizar(self, domicilio: Domicilio) -> None:
        """
        Guarda el estado de la entrega y, si la entrega se cerró, también el
        nuevo estado del pedido (EnCamino -> Entregado). Las dos escrituras
        van en la misma transacción: o se guardan las dos, o ninguna.
        """
        with self.conexion.cursor() as cur:
            cur.execute(
                "UPDATE domicilio SET estado_entrega = %s, fecha_entrega = %s, "
                "motivo_devolucion = %s, id_domiciliario = %s "
                "WHERE id_domicilio = %s",
                (
                    domicilio.estado_entrega,
                    domicilio.fecha_entrega,
                    domicilio.motivo_devolucion,
                    domicilio.id_domiciliario,
                    domicilio.id_domicilio,
                ),
            )
            cur.execute(
                "UPDATE pedido SET estado_pedido = %s WHERE id_pedido = %s",
                (domicilio.pedido.obtenerEstado(), domicilio.pedido.id_pedido),
            )
        self.conexion.commit()