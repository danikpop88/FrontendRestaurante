"""
rutas.py — Capa de rutas para Reservas (RF-11).

PAPEL EN LA ARQUITECTURA: recibe la petición, exige el rol de Administrador y
delega en el GestorReservas. No conoce el repositorio de PostgreSQL: pide su
gestor con obtener_gestor() y es main.py, el punto único de ensamblaje, quien
lo reemplaza por la función que arma el gestor real (app.dependency_overrides).

    GET /api/reservas   solo Administrador   Reservas vigentes (Contratos §8)
"""

from fastapi import APIRouter, Depends

from app.compartido.seguridad import Sesion, requiere_rol
from app.reservas.servicio import GestorReservas

router = APIRouter(prefix="/api/reservas", tags=["Reservas"])


def obtener_gestor() -> GestorReservas:
    """Marcador: main.py lo reemplaza por la función que arma el gestor real."""
    raise NotImplementedError("main.py debe ensamblar el GestorReservas.")


@router.get("")
def listar_reservas(
    sesion: Sesion = Depends(requiere_rol("Administrador")),
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