"""
rutas.py — Capa de rutas (controlador) del componente Cocina.

Las tres rutas de Contratos §4:
    GET  /api/cocina/pedidos                          cola de cocina
    POST /api/cocina/pedidos/{id_pedido}/tomar        Recibido -> EnCocina
    POST /api/cocina/pedidos/{id_pedido}/marcar-listo EnCocina -> EnCamino

Solo Chef (requiere_rol("Chef")). La ruta recibe la Sesion completa y usa
sesion.id_usuario para registrar quién ejecuta el comando (patrón Command).
"""

from typing import Optional

from fastapi import APIRouter, Depends

from app.compartido.seguridad import Sesion, requiere_rol
from app.cocina.servicio import GestorCocina

router = APIRouter(prefix="/api/cocina", tags=["Cocina"])


def obtener_gestor() -> GestorCocina:
    """Marcador: main.py lo reemplaza por la función que arma el gestor real."""
    raise NotImplementedError("main.py debe ensamblar el GestorCocina.")


def _valor_tipo_pedido(tipo) -> str:
    """Devuelve 'EN_RESTAURANTE' o 'DOMICILIO' venga como enum o como str."""
    return tipo.value if hasattr(tipo, "value") else tipo


@router.get("/pedidos")
def ver_cola(
    tipo_pedido: Optional[str] = None,
    sesion: Sesion = Depends(requiere_rol("Chef")),
    gestor: GestorCocina = Depends(obtener_gestor),
):
    pedidos = gestor.ver_cola(tipo_pedido)
    datos = [
        {
            "id_pedido": p.id_pedido,
            "estado_pedido": p.obtener_estado(),
            "tipo_pedido": _valor_tipo_pedido(p.tipo_pedido),
        }
        for p in pedidos
    ]
    return {"total": len(datos), "datos": datos}


@router.post("/pedidos/{id_pedido}/tomar")
def tomar_pedido(
    id_pedido: int,
    sesion: Sesion = Depends(requiere_rol("Chef")),
    gestor: GestorCocina = Depends(obtener_gestor),
):
    pedido = gestor.tomar_pedido(id_pedido, sesion.id_usuario)
    return {
        "id_pedido": pedido.id_pedido,
        "estado_pedido": pedido.obtener_estado(),
    }


@router.post("/pedidos/{id_pedido}/marcar-listo")
def marcar_listo(
    id_pedido: int,
    sesion: Sesion = Depends(requiere_rol("Chef")),
    gestor: GestorCocina = Depends(obtener_gestor),
):
    pedido = gestor.marcar_listo(id_pedido, sesion.id_usuario)
    return {
        "id_pedido": pedido.id_pedido,
        "estado_pedido": pedido.obtener_estado(),
    }