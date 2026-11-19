"""
rutas.py — La capa de rutas (controlador) del componente "Domicilios".

PAPEL EN LA ARQUITECTURA: recibe las peticiones HTTP, valida la forma de los
datos y exige el rol correspondiente. Delega la lógica al GestorDomicilios.
Traduce las excepciones de negocio a códigos HTTP (400, 403, 404, 409).

Rutas (Contratos §5):
    GET   /api/domicilios                                lista mis domicilios (RF-23)
    PATCH /api/domicilios/{id_domicilio}/estado-entrega   cierra la entrega (RF-21)
"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.compartido.seguridad import Sesion, requiere_rol
from app.domicilios.servicio import GestorDomicilios

router = APIRouter(prefix="/api/domicilios", tags=["Domicilios"])


class CerrarEntregaRequest(BaseModel):
    estado_entrega: str
    motivo_devolucion: Optional[str] = None


def obtener_gestor() -> GestorDomicilios:
    """Marcador: main.py lo reemplaza por la función que arma el gestor real."""
    raise NotImplementedError()


@router.get("")
def listar_domicilios(
    sesion: Sesion = Depends(requiere_rol("Domiciliario")),
    gestor: GestorDomicilios = Depends(obtener_gestor),
):
    """RF-23: El domiciliario consulta sus pedidos asignados."""
    domicilios = gestor.listar_mis_domicilios(sesion.id_usuario)

    datos = []
    for d in domicilios:
        datos.append(
            {
                "id_domicilio": d.id_domicilio,
                "id_pedido": d.pedido.id_pedido,
                "estado_pedido": d.pedido.obtener_estado(),
                "estado_entrega": d.estado_entrega,
                "direccion": d.direccion,
                "cliente": {
                    "nombre": d.pedido.cliente.nombre,
                    "telefono": d.pedido.cliente.telefono,
                },
                "total": float(d.pedido.total),
            }
        )
    return {"total": len(datos), "datos": datos}


@router.patch("/{id_domicilio}/estado-entrega")
def actualizar_estado_entrega(
    id_domicilio: int,
    payload: CerrarEntregaRequest,
    sesion: Sesion = Depends(requiere_rol("Domiciliario")),
    gestor: GestorDomicilios = Depends(obtener_gestor),
):
    """RF-21: El domiciliario cierra la entrega y registra el cobro."""
    domicilio = gestor.cerrar_entrega(
        id_domicilio=id_domicilio,
        estado_entrega=payload.estado_entrega,
        motivo_devolucion=payload.motivo_devolucion,
        id_domiciliario=sesion.id_usuario,
    )
    return {
        "estado": 200,
        "mensaje": "Entrega registrada.",
        "estado_pedido": domicilio.pedido.obtener_estado(),
    }