"""
rutas.py — Capa de rutas (controlador) del componente Cocina.

Las tres rutas de Contratos §4:
    GET  /api/cocina/pedidos                          cola de cocina
    POST /api/cocina/pedidos/{id_pedido}/tomar        Recibido -> EnCocina
    POST /api/cocina/pedidos/{id_pedido}/marcar-listo EnCocina -> EnCamino

Solo Chef (requiere_rol("Chef")). La ruta recibe la Sesion completa y usa
sesion.id_usuario para registrar quién ejecuta el comando (patrón Command).
Todas devuelven "el pedido" con el mismo formato de Contratos §3.
"""

from typing import Optional

from fastapi import APIRouter, Depends

from app.cocina.servicio import GestorCocina
from app.compartido.seguridad import Sesion, requiere_rol
from app.pedidos.respuestas import pedido_json

router = APIRouter(prefix="/api/cocina", tags=["Cocina"])


def obtener_gestor() -> GestorCocina:
    """Marcador: main.py lo reemplaza por la función que arma el gestor real."""
    raise NotImplementedError("main.py debe ensamblar el GestorCocina.")


@router.get("/pedidos")
def ver_cola(
    tipo_pedido: Optional[str] = None,
    sesion: Sesion = Depends(requiere_rol("Chef")),
    gestor: GestorCocina = Depends(obtener_gestor),
):
    pedidos = gestor.ver_cola(tipo_pedido)
    return {"total": len(pedidos), "datos": [pedido_json(p) for p in pedidos]}


@router.post("/pedidos/{id_pedido}/tomar")
def tomar_pedido(
    id_pedido: int,
    sesion: Sesion = Depends(requiere_rol("Chef")),
    gestor: GestorCocina = Depends(obtener_gestor),
):
    return pedido_json(gestor.tomar_pedido(id_pedido, sesion.id_usuario))


@router.post("/pedidos/{id_pedido}/marcar-listo")
def marcar_listo(
    id_pedido: int,
    sesion: Sesion = Depends(requiere_rol("Chef")),
    gestor: GestorCocina = Depends(obtener_gestor),
):
    return pedido_json(gestor.marcar_listo(id_pedido, sesion.id_usuario))