"""
rutas.py — Capa de rutas (controlador) para Notificaciones (RF-17, RF-24).

PAPEL EN LA ARQUITECTURA: endpoints para que el front consulte sus avisos
(sondeo) y los marque como leídos. Exige sesión de Mesero o Domiciliario y delega
en el GestorNotificaciones; main.py lo ensambla (app.dependency_overrides).

    GET   /api/notificaciones               Mis avisos (?leido=true|false)
    PATCH /api/notificaciones/{id_aviso}    Marcar como leído (Contratos §6)
"""

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.compartido.seguridad import Sesion, requiere_rol
from app.notificaciones.servicio import GestorNotificaciones

router = APIRouter(prefix="/api/notificaciones", tags=["Notificaciones"])


def obtener_gestor() -> GestorNotificaciones:
    """Marcador: main.py lo reemplaza por la función que arma el gestor real."""
    raise NotImplementedError("main.py debe ensamblar el GestorNotificaciones.")


class MarcarLeidoRequest(BaseModel):
    leido: Literal[True]          # el contrato solo permite marcar como leído


@router.get("")
def listar_avisos(
    leido: bool | None = None,
    sesion: Sesion = Depends(requiere_rol("Mesero", "Domiciliario")),
    gestor: GestorNotificaciones = Depends(obtener_gestor),
):
    avisos = gestor.listar_avisos(sesion.id_usuario, leido)
    return {"total": len(avisos), "datos": avisos}


@router.patch("/{id_aviso}")
def marcar_leido(
    id_aviso: int,
    datos: MarcarLeidoRequest,
    sesion: Sesion = Depends(requiere_rol("Mesero", "Domiciliario")),
    gestor: GestorNotificaciones = Depends(obtener_gestor),
):
    gestor.marcar_como_leido(id_aviso, sesion.id_usuario)
    return {"estado": 200, "mensaje": "Aviso marcado como leído."}