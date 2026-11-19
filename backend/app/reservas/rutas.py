"""
rutas.py — Capa de rutas para Reservas (RF-11).

PAPEL EN LA ARQUITECTURA: recibe la petición HTTP y delega en el gestor.
No conoce el repositorio de PostgreSQL: main.py arma el gestor concreto y lo
inyecta con app.dependency_overrides (Artículo 5).
"""

from fastapi import APIRouter, Depends

from app.compartido.seguridad import Sesion, requiere_rol
from app.reservas.servicio import GestorReservas

router = APIRouter(prefix="/api/reservas", tags=["Reservas"])


def obtener_gestor() -> GestorReservas:
    """Marcador de posición: main.py lo reemplaza con el gestor ensamblado."""
    raise NotImplementedError("main.py debe ensamblar el gestor de reservas.")


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