"""
repositorio_postgres.py — Implementación de IRepositorioProductos con psycopg 3.

PAPEL EN LA ARQUITECTURA: es la ÚNICA pieza del módulo menu/ que escribe SQL
(Artículo 2 de la constitución). Todas las consultas son parametrizadas: los
valores viajan como parámetros (%s con una tupla), nunca concatenados en el
texto SQL (Artículo 6). No decide reglas de negocio: solo guarda y lee, y
reconstruye objetos Producto a partir de las filas.

La conexión se la entrega main.py (una por petición). Las escrituras terminan
con commit(); si algo falla antes, la conexión se cierra y PostgreSQL descarta
los cambios pendientes.
"""

from app.menu.modelos import Producto
from app.menu.repositorio import IRepositorioProductos

# Columnas que se leen siempre, en este orden (el mismo que usa _a_producto).
_COLUMNAS = "id_producto, nombre, descripcion, precio, categoria, disponible, imagen"


def _a_producto(fila: tuple) -> Producto:
    """Convierte una fila de la tabla producto en un objeto Producto."""
    return Producto(
        id_producto=fila[0],
        nombre=fila[1],
        descripcion=fila[2],
        precio=fila[3],          # psycopg entrega NUMERIC como Decimal
        categoria=fila[4],
        disponible=fila[5],
        imagen=fila[6],
    )


class RepositorioProductosPostgres(IRepositorioProductos):
    """Guarda y lee los productos en la tabla producto."""

    def __init__(self, conexion):
        self._conexion = conexion

    def listar(self, categoria: str | None = None) -> list[Producto]:
        with self._conexion.cursor() as cursor:
            if categoria is None:
                cursor.execute(
                    f"SELECT {_COLUMNAS} FROM producto ORDER BY categoria, nombre"
                )
            else:
                cursor.execute(
                    f"SELECT {_COLUMNAS} FROM producto WHERE categoria = %s "
                    "ORDER BY categoria, nombre",
                    (categoria,),
                )
            return [_a_producto(fila) for fila in cursor.fetchall()]

    def obtener_por_id(self, id_producto: int) -> Producto | None:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT {_COLUMNAS} FROM producto WHERE id_producto = %s",
                (id_producto,),
            )
            fila = cursor.fetchone()
        return _a_producto(fila) if fila else None

    def listar_categorias(self) -> list[str]:
        with self._conexion.cursor() as cursor:
            cursor.execute("SELECT DISTINCT categoria FROM producto ORDER BY categoria")
            return [fila[0] for fila in cursor.fetchall()]

    def crear(self, producto: Producto) -> int:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO producto (nombre, descripcion, precio, disponible, categoria, imagen) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_producto",
                (producto.nombre, producto.descripcion, producto.precio,
                 producto.disponible, producto.categoria, producto.imagen),
            )
            id_producto = cursor.fetchone()[0]
        self._conexion.commit()
        return id_producto

    def actualizar(self, producto: Producto) -> None:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE producto SET nombre = %s, descripcion = %s, precio = %s, "
                "disponible = %s, categoria = %s, imagen = %s "
                "WHERE id_producto = %s",
                (producto.nombre, producto.descripcion, producto.precio,
                 producto.disponible, producto.categoria, producto.imagen,
                 producto.id_producto),
            )
        self._conexion.commit()