"""
rutas_ventas.py — Capa de rutas para el reporte de ventas.
"""

from fastapi import APIRouter, Depends
from datetime import date
from pydantic import BaseModel
from app.compartido.seguridad import requiere_rol
from app.compartido.conexion import obtener_conexion
from app.ventas_pagos.servicio_ventas import GestorVentas

router = APIRouter(prefix="/api/ventas-pagos", tags=["Ventas y Pagos"])


def obtener_gestor_ventas(conexion=Depends(obtener_conexion)):
    return GestorVentas(conexion)


@router.get("")
def consultar_ventas(
    desde: date,
    hasta: date,
    id_usuario: int = Depends(requiere_rol(["Administrador"])),
    gestor: GestorVentas = Depends(obtener_gestor_ventas),
):
    try:
        return gestor.consultar_ventas(desde, hasta)
    except ValueError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail=str(e))
