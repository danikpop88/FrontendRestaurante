"""
servicio.py — Las reglas de negocio de la autenticación de usuarios.

PAPEL EN LA ARQUITECTURA: es la capa de negocio del componente "Autenticación de
usuarios" (RF-01 y RF-06). Aquí viven las reglas; la ruta solo recibe la petición
y el repositorio solo guarda y busca (Artículo 3 de la constitución). El servicio
no conoce HTTP: cuando una regla no se cumple lanza una excepción con un mensaje
en español y es main.py quien la traduce a su código (Plan §5.10).

Depende de abstracciones (Artículo 5): recibe un IRepositorioUsuarios, no el de
PostgreSQL, y por eso se puede probar con un repositorio falso en memoria.

Reglas que se aplican aquí:
  - Clave de al menos 12 caracteres, validada ANTES de calcular el hash (RNF-01).
  - Consentimiento explícito para el tratamiento de datos personales (RNF-14).
  - Email único: si ya está registrado, 409.
  - Credenciales inválidas: 401, sin decir cuál de los dos datos falló.

Las funciones validar_* están a nivel de módulo para que la ruta las reutilice al
validar la forma de la petición (422) y la regla quede escrita en UN solo lugar.
Cuando falla una, lanzan ValueError con el mensaje que verá el usuario.
"""

from app.autenticacion.modelos import Cliente, IEmpleado, IUsuario
from app.autenticacion.repositorio import IRepositorioUsuarios
from app.compartido.excepciones import (
    NoAutenticadoError,
    NoEncontradoError,
    ReglaNegocioError,
    SinPermisoError,
)
from app.compartido.seguridad import GestorSesiones, hashear_clave, verificar_clave

LONGITUD_MINIMA_CLAVE = 12


def validar_contrasena(contrasena: str) -> str:
    """RNF-01: la clave debe tener al menos 12 caracteres."""
    if len(contrasena) < LONGITUD_MINIMA_CLAVE:
        raise ValueError(
            f"La contraseña debe tener al menos {LONGITUD_MINIMA_CLAVE} caracteres."
        )
    return contrasena


def validar_consentimiento(acepta_tratamiento_datos: bool) -> bool:
    """RNF-14: el cliente debe aceptar el tratamiento de sus datos antes de registrarse."""
    if acepta_tratamiento_datos is not True:
        raise ValueError("Debe aceptar el tratamiento de datos personales.")
    return acepta_tratamiento_datos


def validar_direccion(direccion: str) -> str:
    """RF-06: la dirección de entrega es obligatoria y no puede ir vacía."""
    if not direccion.strip():
        raise ValueError("La dirección es obligatoria.")
    return direccion.strip()


class GestorAutenticacion:

    def __init__(self, repositorio: IRepositorioUsuarios, sesiones: GestorSesiones,
                 clases_empleado: dict[str, type[IEmpleado]]):
        self._repositorio = repositorio
        self._sesiones = sesiones
        self._clases_empleado = clases_empleado     # tipo_cargo -> clase concreta (la arma main.py)

    def registrar_cliente(self, nombre: str, telefono: str, email: str, contrasena: str,
                          acepta_tratamiento_datos: bool, direccion: str | None = None) -> Cliente:
        """RF-01: el cliente crea su propia cuenta."""
        validar_contrasena(contrasena)                  # antes de calcular el hash
        validar_consentimiento(acepta_tratamiento_datos)
        self._exigir_email_libre(email)
        cliente = Cliente(None, nombre, telefono, email, hashear_clave(contrasena), direccion)
        return self._repositorio.guardar_cliente(cliente)

    def crear_empleado(self, nombre: str, telefono: str, email: str, contrasena: str,
                       tipo_cargo: str) -> IEmpleado:
        """RF-01: el administrador crea la cuenta de un empleado (el rol lo exige la ruta, RN-09)."""
        validar_contrasena(contrasena)
        clase = self._clases_empleado.get(tipo_cargo)
        if clase is None:
            raise ReglaNegocioError("Todavía no se pueden crear cuentas de ese cargo.")
        self._exigir_email_libre(email)
        empleado = clase(None, nombre, telefono, email, hashear_clave(contrasena), None, True)
        return self._repositorio.guardar_empleado(empleado)

    def iniciar_sesion(self, email: str, contrasena: str) -> tuple[str, IUsuario]:
        """Usuario.iniciarSesion(): devuelve el token de la sesión y el usuario."""
        usuario = self._repositorio.buscar_por_email(email)
        if usuario is None or not verificar_clave(contrasena, usuario.contrasena):
            # El mismo mensaje en los dos casos: no se revela cuál dato falló.
            raise NoAutenticadoError("Credenciales inválidas.")
        token = self._sesiones.crear(usuario.id_usuario, usuario.obtener_rol())
        return token, usuario

    def cerrar_sesion(self, token: str) -> None:
        """Usuario.cerrarSesion(): el token deja de valer."""
        self._sesiones.cerrar(token)

    def guardar_direccion(self, id_usuario: int, direccion: str) -> None:
        """RF-06: Cliente.registrarDireccion() y modificarDireccion() (reemplaza la anterior)."""
        usuario = self._repositorio.buscar_por_id(id_usuario)
        if usuario is None:
            raise NoEncontradoError("El usuario no existe.")
        if not isinstance(usuario, Cliente):
            raise SinPermisoError("Solo un cliente tiene dirección de entrega.")
        usuario.modificar_direccion(validar_direccion(direccion))
        self._repositorio.guardar_direccion(usuario)

    def _exigir_email_libre(self, email: str) -> None:
        if self._repositorio.buscar_por_email(email) is not None:
            raise ReglaNegocioError("El correo ya está registrado.")