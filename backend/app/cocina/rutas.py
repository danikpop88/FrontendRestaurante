"""
rutas.py — Capa de rutas (controlador) del componente Cocina.
"""

from fastapi import APIRouter, Depends
from typing import Optional
from app.compartido.seguridad import requiere_rol
from app.cocina.servicio import GestorCocina

router = APIRouter(prefix="/api/cocina", tags=["Cocina"])


def obtener_gestor() -> GestorCocina:
    raise NotImplementedError()


@router.get("/pedidos")
def ver_cola(
    tipo_pedido: Optional[str] = None,
    id_usuario: int = Depends(requiere_rol(["Chef"])),
    gestor: GestorCocina = Depends(obtener_gestor),
):
    pedidos = gestor.ver_cola(tipo_pedido)
    datos = [
        {
            "id_pedido": p.id_pedido,
            "estado_pedido": p.obtener_estado(),
            "tipo_pedido": p.tipo_pedido.value,
        }
        for p in pedidos
    ]
    return {"total": len(datos), "datos": datos}


@router.post("/pedidos/{id_pedido}/tomar")
def tomar_pedido(
    id_pedido: int,
    id_usuario: int = Depends(requiere_rol(["Chef"])),
    gestor: GestorCocina = Depends(obtener_gestor),
):
    pedido = gestor.tomar_pedido(id_pedido, id_usuario)
    return {"id_pedido": pedido.id_pedido, "estado_pedido": pedido.obtener_estado()}


@router.post("/pedidos/{id_pedido}/marcar-listo")
def marcar_listo(
    id_pedido: int,
    id_usuario: int = Depends(requiere_rol(["Chef"])),
    gestor: GestorCocina = Depends(obtener_gestor),
):
    pedido = gestor.marcar_listo(id_pedido, id_usuario)
    return {"id_pedido": pedido.id_pedido, "estado_pedido": pedido.obtener_estado()}
