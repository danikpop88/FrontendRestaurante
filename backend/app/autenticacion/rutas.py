"""
rutas.py — Las cinco rutas HTTP de la autenticación de usuarios (Contratos §1).

PAPEL EN LA ARQUITECTURA: es la capa de rutas (el controlador) del componente
"Autenticación de usuarios". Hace tres cosas y nada más: recibe la petición,
valida su FORMA (campos obligatorios, tipos y las reglas de entrada, con
Pydantic: si falla, FastAPI responde 422) y delega en el GestorAutenticacion.
No contiene reglas de negocio ni SQL (Artículo 3 y Artículo 2 de la constitución).

Rutas (todas bajo /api/autenticacion):
    POST   /registro    público              El cliente crea su cuenta (201)
    POST   /empleados   solo Administrador   Crea cuentas del personal (201, RN-09)
    POST   /sesion      público              Iniciar sesión (200)
    DELETE /sesion      con sesión           Cerrar sesión (200)
    PUT    /direccion   solo Cliente         Guardar la dirección de entrega (200)

Cómo obtiene el gestor: la ruta no sabe qué repositorio ni qué clases concretas
se usan. Pide obtener_gestor() y es main.py, el punto único de ensamblaje, quien
la reemplaza por la función que arma el gestor real con la conexión de cada
petición (app.dependency_overrides).
"""

from typing import Literal

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field, field_validator

from app.autenticacion.servicio import (
    GestorAutenticacion,
    validar_consentimiento,
    validar_contrasena,
    validar_direccion,
)
from app.compartido.seguridad import Sesion, extraer_token, requiere_rol

router = APIRouter(prefix="/api/autenticacion", tags=["Autenticación de usuarios"])


def obtener_gestor() -> GestorAutenticacion:
    """Marcador: main.py lo reemplaza por la función que arma el gestor real."""
    raise NotImplementedError("main.py debe ensamblar el GestorAutenticacion.")


# =====================================================================
# Cuerpos de las peticiones. Las reglas de entrada se reutilizan del servicio
# para que cada regla esté escrita en un solo lugar.
# =====================================================================

class RegistroEntrada(BaseModel):
    nombre: str = Field(min_length=1)
    telefono: str = Field(min_length=1)
    email: str = Field(min_length=1)
    contrasena: str
    acepta_tratamiento_datos: bool
    direccion: str | None = None

    @field_validator("contrasena")
    @classmethod
    def clave_larga(cls, valor: str) -> str:
        return validar_contrasena(valor)

    @field_validator("acepta_tratamiento_datos")
    @classmethod
    def consentimiento(cls, valor: bool) -> bool:
        return validar_consentimiento(valor)


class EmpleadoEntrada(BaseModel):
    nombre: str = Field(min_length=1)
    telefono: str = Field(min_length=1)
    email: str = Field(min_length=1)
    contrasena: str
    tipo_cargo: Literal["Chef", "Mesero", "Domiciliario", "Administrador"]

    @field_validator("contrasena")
    @classmethod
    def clave_larga(cls, valor: str) -> str:
        return validar_contrasena(valor)


class SesionEntrada(BaseModel):
    email: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)


class DireccionEntrada(BaseModel):
    direccion: str

    @field_validator("direccion")
    @classmethod
    def direccion_con_texto(cls, valor: str) -> str:
        return validar_direccion(valor)


# =====================================================================
# Rutas
# =====================================================================

@router.post("/registro", status_code=201)
def registrar_cliente(cuerpo: RegistroEntrada, gestor: GestorAutenticacion = Depends(obtener_gestor)):
    cliente = gestor.registrar_cliente(
        cuerpo.nombre, cuerpo.telefono, cuerpo.email, cuerpo.contrasena,
        cuerpo.acepta_tratamiento_datos, cuerpo.direccion,
    )
    return {"estado": 201, "mensaje": "Cuenta creada exitosamente.", "id_usuario": cliente.id_usuario}


@router.post("/empleados", status_code=201)
def crear_empleado(
    cuerpo: EmpleadoEntrada,
    gestor: GestorAutenticacion = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol("Administrador")),      # RN-09
):
    empleado = gestor.crear_empleado(
        cuerpo.nombre, cuerpo.telefono, cuerpo.email, cuerpo.contrasena, cuerpo.tipo_cargo,
    )
    return {
        "estado": 201,
        "mensaje": "Cuenta creada exitosamente.",
        "id_usuario": empleado.id_usuario,
        "id_empleado": empleado.id_empleado,
    }


@router.post("/sesion")
def iniciar_sesion(cuerpo: SesionEntrada, gestor: GestorAutenticacion = Depends(obtener_gestor)):
    token, usuario = gestor.iniciar_sesion(cuerpo.email, cuerpo.contrasena)
    return {
        "token": token,
        "rol": usuario.obtener_rol(),
        "usuario": {
            "id_usuario": usuario.id_usuario,
            "nombre": usuario.nombre,
            "direccion": getattr(usuario, "direccion", None),     # solo los clientes tienen dirección
        },
    }


@router.delete("/sesion")
def cerrar_sesion(
    gestor: GestorAutenticacion = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol()),                     # exige una sesión válida
    authorization: str | None = Header(default=None),
):
    gestor.cerrar_sesion(extraer_token(authorization))
    return {"estado": 200, "mensaje": "Sesión cerrada."}


@router.put("/direccion")
def guardar_direccion(
    cuerpo: DireccionEntrada,
    gestor: GestorAutenticacion = Depends(obtener_gestor),
    sesion: Sesion = Depends(requiere_rol("Cliente")),
):
    # La dirección se guarda al usuario de la SESIÓN, nunca a un id enviado por el cliente.
    gestor.guardar_direccion(sesion.id_usuario, cuerpo.direccion)
    return {"estado": 200, "mensaje": "Dirección guardada."}