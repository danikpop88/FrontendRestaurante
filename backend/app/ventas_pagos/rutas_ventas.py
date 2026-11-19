"""
rutas_ventas.py — Capa de rutas del reporte de ventas (RF-10, RN-10).

PAPEL EN LA ARQUITECTURA: recibe la petición HTTP, exige el rol Administrador y
delega en el gestor. No conoce PostgreSQL: main.py arma el gestor concreto y lo
inyecta con app.dependency_overrides (Artículo 5).
"""

from datetime import date

from fastapi import APIRouter, Depends

from app.compartido.seguridad import Sesion, requiere_rol
from app.ventas_pagos.servicio_ventas import GestorVentas

router = APIRouter(prefix="/api/ventas-pagos", tags=["Ventas y Pagos"])


def obtener_gestor_ventas() -> GestorVentas:
    """Marcador de posición: main.py lo reemplaza con el gestor ensamblado."""
    raise NotImplementedError("main.py debe ensamblar el gestor de ventas.")


@router.get("")
def consultar_ventas(
    desde: date,
    hasta: date,
    sesion: Sesion = Depends(requiere_rol("Administrador")),
    gestor: GestorVentas = Depends(obtener_gestor_ventas),
):
    return gestor.consultar_ventas(desde, hasta)