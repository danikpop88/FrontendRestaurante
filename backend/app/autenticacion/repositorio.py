"""
repositorio.py — El contrato de acceso a datos de los usuarios.

PAPEL EN LA ARQUITECTURA: es la clase abstracta (ABC) que define qué
operaciones necesita la capa de negocio sobre los usuarios. El
GestorAutenticacion (servicio.py) depende de esta abstracta y nunca de la
implementación concreta: así se puede cambiar PostgreSQL por otro motor, o por
un repositorio falso en las pruebas, sin tocar las reglas (Artículo 5 de la
constitución). La implementación real está en repositorio_postgres.py y es la
única que ejecuta SQL (Artículo 2).

Los métodos reciben y devuelven clases de dominio (modelos.py), no filas sueltas.
Aquí no hay reglas de negocio: el repositorio guarda y busca, nada más.
"""

from abc import ABC, abstractmethod

from app.autenticacion.modelos import Cliente, IEmpleado, IUsuario


class IRepositorioUsuarios(ABC):
    """Operaciones de persistencia sobre la tabla usuario."""

    @abstractmethod
    def buscar_por_email(self, email: str) -> IUsuario | None:
        """Devuelve el usuario con ese email, o None si no existe."""

    @abstractmethod
    def buscar_por_id(self, id_usuario: int) -> IUsuario | None:
        """Devuelve el usuario con ese identificador, o None si no existe."""

    @abstractmethod
    def guardar_cliente(self, cliente: Cliente) -> Cliente:
        """
        Guarda un cliente nuevo y lo devuelve con su id_usuario ya asignado.
        La contrasena del cliente debe llegar ya convertida en hash.
        """

    @abstractmethod
    def guardar_empleado(self, empleado: IEmpleado) -> IEmpleado:
        """
        Guarda un empleado nuevo y lo devuelve con su id_usuario y su
        id_empleado asignados (el id_empleado lo asigna el repositorio al
        crear la cuenta). La contrasena debe llegar ya convertida en hash.
        """

    @abstractmethod
    def guardar_direccion(self, cliente: Cliente) -> None:
        """Guarda la dirección actual del cliente (RF-06)."""