"""
servicio.py — GestorMenu: las reglas de negocio del componente "Menú y productos".

PAPEL EN LA ARQUITECTURA: es la capa de negocio del módulo (Artículo 3 de la
constitución). No conoce HTTP ni SQL: recibe datos ya tipados desde la ruta,
aplica las reglas y le pide al repositorio (el contrato IRepositorioProductos)
que guarde o lea. Lanza excepciones con mensajes en español; main.py las
traduce a su código HTTP (Plan §5.10).

Reglas que aplica:
  - RN-09: solo el rol Administrador crea, edita o cambia la disponibilidad de
    un producto (SinPermisoError -> 403). La ruta también lo exige con
    requiere_rol; aquí se verifica de nuevo porque el backend no debe confiar
    en una sola barrera.
  - Datos válidos (ValidacionError -> 422, con todos los motivos juntos):
    nombre no vacío, precio no negativo y categoría que ya exista en el menú.
  - Producto inexistente (NoEncontradoError -> 404).

Las funciones validar_* están a nivel de módulo para que la ruta las reutilice
al validar la forma de la petición, y cada regla quede escrita en UN solo lugar
(mismo patrón que el módulo de autenticación). Si falla una, lanzan ValueError
con el mensaje que verá el usuario.
"""

from decimal import Decimal

from app.compartido.excepciones import NoEncontradoError, SinPermisoError, ValidacionError
from app.menu.modelos import Producto
from app.menu.repositorio import IRepositorioProductos

ROL_ADMINISTRADOR = "Administrador"
LONGITUD_MAXIMA_NOMBRE = 100              # igual que producto.nombre VARCHAR(100)
PRECIO_MAXIMO = Decimal("9999999999.99")  # lo que cabe en NUMERIC(12,2)


def validar_nombre(nombre: str) -> str:
    """El nombre del producto es obligatorio y cabe en la columna."""
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre del producto es obligatorio.")
    if len(nombre) > LONGITUD_MAXIMA_NOMBRE:
        raise ValueError(f"El nombre no puede superar {LONGITUD_MAXIMA_NOMBRE} caracteres.")
    return nombre


def validar_precio(precio: Decimal) -> Decimal:
    """El precio no puede ser negativo (puede ser 0) y debe caber en NUMERIC(12,2)."""
    if not precio.is_finite():
        raise ValueError("El precio no es válido.")
    if precio < 0:
        raise ValueError("El precio no puede ser negativo.")
    if precio > PRECIO_MAXIMO:
        raise ValueError("El precio es demasiado alto.")
    if precio.as_tuple().exponent < -2:
        raise ValueError("El precio admite como máximo 2 decimales.")
    return precio


def _texto_opcional(texto: str | None) -> str | None:
    """Quita espacios sobrantes; un texto vacío se guarda como vacío (None)."""
    if texto is None:
        return None
    texto = texto.strip()
    return texto or None


class GestorMenu:

    def __init__(self, repositorio: IRepositorioProductos):
        self._repositorio = repositorio

    # ------------------------------------------------------------ consulta
    def listar_productos(self, categoria: str | None = None) -> list[Producto]:
        """RF-02: el menú, con filtro opcional por categoría. Una categoría sin productos da lista vacía."""
        return self._repositorio.listar(categoria)

    # ---------------------------------------------------- escrituras (RN-09)
    def crear_producto(self, rol: str, nombre: str, categoria: str, precio: Decimal,
                       descripcion: str | None = None, imagen: str | None = None) -> Producto:
        """RF-13: el administrador crea un producto nuevo (nace disponible)."""
        self._exigir_administrador(rol)
        nombre, categoria, precio = self._validar_datos(nombre, categoria, precio)
        producto = Producto(None, nombre, _texto_opcional(descripcion), precio,
                            categoria, True, _texto_opcional(imagen))
        producto.id_producto = self._repositorio.crear(producto)
        return producto

    def editar_producto(self, rol: str, id_producto: int, nombre: str, categoria: str,
                        precio: Decimal, descripcion: str | None = None) -> Producto:
        """RF-12: el administrador edita nombre, categoría, precio y descripción (no la disponibilidad)."""
        self._exigir_administrador(rol)
        producto = self._obtener(id_producto)
        nombre, categoria, precio = self._validar_datos(nombre, categoria, precio)
        producto.nombre = nombre
        producto.categoria = categoria
        producto.precio = precio
        producto.descripcion = _texto_opcional(descripcion)
        self._repositorio.actualizar(producto)
        return producto

    def cambiar_disponibilidad(self, rol: str, id_producto: int, disponible: bool) -> Producto:
        """RF-14: el administrador marca un producto como Agotado (False) o lo deja disponible (True)."""
        self._exigir_administrador(rol)
        producto = self._obtener(id_producto)
        producto.actualizar_disponibilidad(disponible)
        self._repositorio.actualizar(producto)
        return producto

    # ------------------------------------------------------------ internos
    def _exigir_administrador(self, rol: str) -> None:
        if rol != ROL_ADMINISTRADOR:
            raise SinPermisoError("Solo el administrador puede modificar el menú.")

    def _obtener(self, id_producto: int) -> Producto:
        producto = self._repositorio.obtener_por_id(id_producto)
        if producto is None:
            raise NoEncontradoError("El producto no existe.")
        return producto

    def _validar_datos(self, nombre: str, categoria: str, precio: Decimal) -> tuple[str, str, Decimal]:
        """Valida nombre, precio y categoría juntos, para devolver todos los motivos a la vez."""
        errores: list[str] = []
        try:
            nombre = validar_nombre(nombre)
        except ValueError as error:
            errores.append(str(error))
        try:
            precio = validar_precio(precio)
        except ValueError as error:
            errores.append(str(error))
        categoria = categoria.strip()
        if categoria not in self._repositorio.listar_categorias():
            errores.append("La categoría no existe en el menú.")
        if errores:
            raise ValidacionError(errores)
        return nombre, categoria, precio