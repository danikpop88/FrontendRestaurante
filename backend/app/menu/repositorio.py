"""
repositorio.py — El contrato de acceso a datos del componente "Menú y productos".

PAPEL EN LA ARQUITECTURA: es la clase abstracta (ABC) que el GestorMenu conoce.
El servicio no sabe si detrás hay PostgreSQL o una lista en memoria (como en las
pruebas): depende de esta abstracción y no de la implementación concreta
(inversión de dependencias, Artículo 5 de la constitución). Aquí no hay reglas
de negocio: el repositorio guarda y busca, nada más.
"""

from abc import ABC, abstractmethod

from app.menu.modelos import Producto


class IRepositorioProductos(ABC):
    """Lo que el servicio necesita poder hacer con los productos guardados."""

    @abstractmethod
    def listar(self, categoria: str | None = None) -> list[Producto]:
        """Devuelve los productos; si se indica la categoría, solo los de esa categoría."""

    @abstractmethod
    def obtener_por_id(self, id_producto: int) -> Producto | None:
        """Devuelve el producto, o None si no existe."""

    @abstractmethod
    def listar_categorias(self) -> list[str]:
        """Devuelve las categorías que ya existen en el menú (sin repetir)."""

    @abstractmethod
    def crear(self, producto: Producto) -> int:
        """Guarda un producto nuevo y devuelve su id_producto."""

    @abstractmethod
    def actualizar(self, producto: Producto) -> None:
        """Guarda los cambios de un producto que ya existe."""