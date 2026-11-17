"""
modelos.py — La clase de dominio del componente "Menú y productos".

PAPEL EN LA ARQUITECTURA: es la clase Producto del nivel 4 del C4. Solo guarda
los datos de un producto del menú y sabe cambiar su disponibilidad; no contiene
SQL (eso es del repositorio) ni las validaciones de negocio como el precio o la
categoría (eso es del servicio, Artículo 3 de la constitución).

Un producto con disponible = False es un producto "Agotado" (RN-05): se ve
bloqueado en el menú y no se puede agregar a un pedido.

Convenciones (Artículo 11): atributos en snake_case. Producto.actualizarDisponibilidad()
del diagrama es actualizar_disponibilidad(). El precio es Decimal porque
PostgreSQL entrega NUMERIC(12,2) como Decimal y el dinero debe ser exacto.
"""

from decimal import Decimal


class Producto:
    """Un plato o bebida del menú."""

    def __init__(self, id_producto: int | None, nombre: str, descripcion: str | None,
                 precio: Decimal, categoria: str, disponible: bool = True,
                 imagen: str | None = None):
        self.id_producto = id_producto    # None mientras el producto aún no se guarda en la base
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.categoria = categoria
        self.disponible = disponible      # False = "Agotado" (RN-05)
        self.imagen = imagen              # ruta de la foto del producto

    def actualizar_disponibilidad(self, disponible: bool) -> None:
        """Producto.actualizarDisponibilidad() del diagrama: marca el producto como disponible o agotado."""
        self.disponible = disponible