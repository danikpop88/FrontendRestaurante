"""
rutas_ventas.py — Capa de rutas para el reporte de ventas (RF-10).

PAPEL EN LA ARQUITECTURA: recibe la petición, exige el rol Administrador (RN-10)
y delega en el GestorVentas. No conoce la base de datos: pide su gestor con
obtener_gestor() y main.py lo reemplaza por el que arma el gestor real.

    GET /api/ventas-pagos?desde=AAAA-MM-DD&hasta=AAAA-MM-DD   solo Administrador
"""

from datetime import date

from fastapi import APIRouter, Depends

from app.compartido.seguridad import Sesion, requiere_rol
from app.ventas_pagos.servicio_ventas import GestorVentas

router = APIRouter(prefix="/api/ventas-pagos", tags=["Ventas y Pagos"])


def obtener_gestor() -> GestorVentas:
    """Marcador: main.py lo reemplaza por la función que arma el gestor real."""
    raise NotImplementedError("main.py debe ensamblar el GestorVentas.")


@router.get("")
def consultar_ventas(
    desde: date,
    hasta: date,
    sesion: Sesion = Depends(requiere_rol("Administrador")),
    gestor: GestorVentas = Depends(obtener_gestor),
):
    return gestor.consultar_ventas(desde, hasta)