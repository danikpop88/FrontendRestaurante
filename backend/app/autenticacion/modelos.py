"""
modelos.py — Las clases de dominio del componente "Autenticación de usuarios".

PAPEL EN LA ARQUITECTURA: son las clases del nivel 4 del C4 para este
componente. Solo guardan datos y saben decir qué rol tienen; no contienen SQL
(eso es del repositorio) ni reglas de negocio como el largo de la clave (eso es
del servicio, Artículo 3 de la constitución).

Jerarquía del diagrama:

    IUsuario (abstracta)
      ├── Cliente
      └── IEmpleado (abstracta)
            ├── Mesero
            ├── Domiciliario
            └── Administrador

(El Chef también es un empleado, pero pertenece al componente Cocina y se crea
en la Fase 7.)

Convenciones (Artículo 11): clases abstractas con prefijo I y heredando de ABC;
atributos en snake_case, sin tildes ni ñ (Usuario.contraseña del diagrama es
contrasena, y guarda siempre el HASH, nunca la clave en texto plano).

Los métodos iniciarSesion() y cerrarSesion() del diagrama los cumple el
GestorAutenticacion (servicio.py) con las rutas de sesión.
"""

from abc import ABC, abstractmethod


class IUsuario(ABC):
    """Usuario del sistema: tiene lo común a clientes y empleados."""

    def __init__(self, id_usuario: int | None, nombre: str, telefono: str,
                 email: str, contrasena: str):
        self.id_usuario = id_usuario    # None mientras el usuario aún no se guarda en la base
        self.nombre = nombre
        self.telefono = telefono
        self.email = email
        self.contrasena = contrasena    # el hash scrypt, nunca la clave en texto plano

    @abstractmethod
    def obtener_rol(self) -> str:
        """Devuelve el rol del usuario: Cliente, Mesero, Domiciliario, etc."""


class Cliente(IUsuario):
    """Persona que se registra sola y hace pedidos a domicilio."""

    def __init__(self, id_usuario: int | None, nombre: str, telefono: str,
                 email: str, contrasena: str, direccion: str | None = None):
        super().__init__(id_usuario, nombre, telefono, email, contrasena)
        self.direccion = direccion

    def registrar_direccion(self, direccion: str) -> None:
        """Cliente.registrarDireccion() del diagrama (RF-06)."""
        self.direccion = direccion

    def modificar_direccion(self, direccion: str) -> None:
        """Cliente.modificarDireccion() del diagrama: reemplaza la dirección guardada."""
        self.registrar_direccion(direccion)

    def obtener_rol(self) -> str:
        return "Cliente"


class IEmpleado(IUsuario):
    """Persona del personal: Chef, Mesero, Domiciliario o Administrador."""

    def __init__(self, id_usuario: int | None, nombre: str, telefono: str,
                 email: str, contrasena: str, id_empleado: int | None, estado: bool = True):
        super().__init__(id_usuario, nombre, telefono, email, contrasena)
        self.id_empleado = id_empleado  # se asigna al crear la cuenta del empleado
        self.estado = estado            # falso = el empleado no está activo

    @property
    def tipo_cargo(self) -> str:
        """Empleado.tipoCargo del diagrama: es el mismo texto que el rol."""
        return self.obtener_rol()


class Mesero(IEmpleado):
    """Toma comandas en el salón y recibe el aviso de plato listo."""

    def obtener_rol(self) -> str:
        return "Mesero"


class Domiciliario(IEmpleado):
    """Lleva los pedidos a domicilio y cierra la entrega."""

    def obtener_rol(self) -> str:
        return "Domiciliario"


class Administrador(IEmpleado):
    """Administra el menú y consulta ventas, pagos y reservas."""

    def obtener_rol(self) -> str:
        return "Administrador"