"""
rutas.py — Las cuatro rutas HTTP del menú y productos (Contratos §2).

PAPEL EN LA ARQUITECTURA: es la capa de rutas (el controlador) del componente
"Menú y productos". Recibe la petición, valida su FORMA con Pydantic (campos
obligatorios, tipos y las reglas de entrada que reutiliza del servicio: si
falla, 422) y delega en el GestorMenu. No contiene reglas de negocio ni SQL
(Artículo 3 y Artículo 2 de la constitución).

Rutas (todas bajo /api/menu):
    GET   /productos                              cualquier usuario con sesión   RF-02
    POST  /productos                              solo Administrador (201)       RF-13
    PUT   /productos/{id_producto}                solo Administrador             RF-12
    PATCH /productos/{id_producto}/disponibilidad solo Administrador             RF-14

Cómo obtiene el gestor: igual que la autenticación. La ruta pide obtener_gestor()
y main.py, el punto único de ensamblaje, la reemplaza con app.dependency_overrides.

Nota: no hay ruta para eliminar productos (el MVP solo los crea, edita y marca
como Agotado: RF-12, RF-13 y RF-14).
"""

from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, StrictBool, field_validator

from app.compartido.seguridad import Sesion, requiere_rol
from app.menu.modelos import Producto
from app.menu.servicio import GestorMenu, validar_nombre, validar_precio

router = APIRouter(prefix="/api/menu", tags=["Menú y productos"])


def obtener_gestor() -> GestorMenu:
    """Marcador: main.py lo reemplaza por la función que arma el gestor real."""
    raise NotImplementedError("main.py debe ensamblar el GestorMenu.")


# =====================================================================
# Cuerpos de las peticiones (las reglas de entrada vienen del servicio)
# =====================================================================

class ProductoEditableEntrada(BaseModel):
    """Los campos editables completos (RF-12). La disponibilidad no se cambia aquí."""
    nombre: str
    categoria: str = Field(min_length=1, max_length=50)
    precio: Decimal
    descripcion: str | None = Field(default=None, max_length=300)

    @field_validator("nombre")
    @classmethod
    def nombre_valido(cls, valor: str) -> str:
        return validar_nombre(valor)

    @field_validator("precio")
    @classmethod
    def precio_valido(cls, valor: Decimal) -> Decimal:
        return validar_precio(valor)


class ProductoNuevoEntrada(ProductoEditableEntrada):
    """Crear un producto (RF-13): lo mismo, más la ruta de la foto (opcional)."""
    imagen: str | None = Field(default=None, max_length=200)


class DisponibilidadEntrada(BaseModel):
    disponible: StrictBool      # estricto: solo true o false, no "si" ni 1


def _a_json(producto: Producto) -> dict:
    """El producto como lo muestran los Contratos §2 (el precio, como número)."""
    return {
        "id_producto": producto.id_producto,
        "nombre": producto.nombre,
        "descripcion": producto.descripcion,
        "precio": float(producto.precio),
        "disponible": producto.disponible,
        "categoria": producto.categoria,
        "imagen": producto.imagen,
    }


# =====================================================================
# Rutas
# =====================================================================

@router.get("/productos")
def consultar_menu(
    categoria: str | None = None,
    gestor: GestorMenu = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol()),                     # cualquier usuario con sesión
):
    productos = gestor.listar_productos(categoria)
    return {"total": len(productos), "datos": [_a_json(p) for p in productos]}


@router.post("/productos", status_code=201)
def crear_producto(
    cuerpo: ProductoNuevoEntrada,
    gestor: GestorMenu = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol("Administrador")),      # RN-09
):
    producto = gestor.crear_producto(
        sesion.rol, cuerpo.nombre, cuerpo.categoria, cuerpo.precio,
        cuerpo.descripcion, cuerpo.imagen,
    )
    return {"estado": 201, "mensaje": "Producto creado exitosamente.", "id_producto": producto.id_producto}


@router.put("/productos/{id_producto}")
def editar_producto(
    id_producto: int,
    cuerpo: ProductoEditableEntrada,
    gestor: GestorMenu = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol("Administrador")),      # RN-09
):
    gestor.editar_producto(
        sesion.rol, id_producto, cuerpo.nombre, cuerpo.categoria, cuerpo.precio, cuerpo.descripcion,
    )
    return {"estado": 200, "mensaje": "Producto actualizado exitosamente."}


@router.patch("/productos/{id_producto}/disponibilidad")
def cambiar_disponibilidad(
    id_producto: int,
    cuerpo: DisponibilidadEntrada,
    gestor: GestorMenu = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol("Administrador")),      # RN-09
):
    gestor.cambiar_disponibilidad(sesion.rol, id_producto, cuerpo.disponible)
    mensaje = "Producto marcado como disponible." if cuerpo.disponible else "Producto marcado como agotado."
    return {"estado": 200, "mensaje": mensaje}