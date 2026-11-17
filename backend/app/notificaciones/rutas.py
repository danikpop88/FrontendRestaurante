"""
rutas.py — Capa de rutas (controlador) para Notificaciones.

PAPEL EN LA ARQUITECTURA: endpoints para que el frontend consulte los avisos
(sondeo) y los marque como leídos.
"""

from fastapi import APIRouter, Depends
from typing import Optional
from pydantic import BaseModel
from app.compartido.seguridad import requiere_rol
from app.notificaciones.repositorio import IRepositorioAvisos

router = APIRouter(prefix="/api/notificaciones", tags=["Notificaciones"])


def obtener_repositorio_avisos() -> IRepositorioAvisos:
    raise NotImplementedError()


class MarcarLeidoRequest(BaseModel):
    leido: bool


@router.get("")
def listar_avisos(
    leido: Optional[bool] = None,
    id_usuario: int = Depends(requiere_rol(["Mesero", "Domiciliario"])),
    repo: IRepositorioAvisos = Depends(obtener_repositorio_avisos),
):
    avisos = repo.listar_por_usuario(id_usuario, leido)
    return {"total": len(avisos), "datos": avisos}


@router.patch("/{id_aviso}")
def marcar_leido(
    id_aviso: int,
    payload: MarcarLeidoRequest,
    id_usuario: int = Depends(requiere_rol(["Mesero", "Domiciliario"])),
    repo: IRepositorioAvisos = Depends(obtener_repositorio_avisos),
):
    repo.marcar_como_leido(id_aviso, id_usuario)
    return {"estado": 200, "mensaje": "Aviso marcado como leído."}
