"""
rutas.py — Capa de rutas para Reservas.
"""

from fastapi import APIRouter, Depends
from typing import List
from app.compartido.seguridad import requiere_rol
from app.reservas.servicio import GestorReservas
from app.reservas.repositorio_postgres import RepositorioReservasPostgres
from app.compartido.conexion import obtener_conexion

router = APIRouter(prefix="/api/reservas", tags=["Reservas"])


def obtener_gestor(conexion=Depends(obtener_conexion)):
    return GestorReservas(RepositorioReservasPostgres(conexion))


@router.get("")
def listar_reservas(
    id_usuario: int = Depends(requiere_rol(["Administrador"])),
    gestor: GestorReservas = Depends(obtener_gestor),
):
    reservas = gestor.listar_vigentes()
    datos = []
    for r in reservas:
        datos.append(
            {
                "id_reserva": r.id_reserva,
                "nombre_titular": r.nombre_titular,
                "telefono_titular": r.telefono_titular,
                "fecha_reserva": r.fecha_reserva.isoformat(),
                "hora_reserva": r.hora_reserva.isoformat(),
                "numero_mesa": r.mesa.numero_mesa,
            }
        )
    return {"total": len(datos), "datos": datos}
