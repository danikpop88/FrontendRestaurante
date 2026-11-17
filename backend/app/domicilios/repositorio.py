"""
repositorio.py — El contrato de acceso a datos para "Domicilios".

PAPEL EN LA ARQUITECTURA: es la clase abstracta (interfaz) que define qué
operaciones de base de datos existen para los domicilios. El GestorDomicilios
(servicio) dependerá de esta interfaz y no de la implementación real,
cumpliendo con el principio de inversión de dependencias (SOLID).

El método obtener_menos_pedidos_activos() es clave para la asignación
automática que exige el MVP (RF-24).
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.domicilios.modelos import Domicilio


class IRepositorioDomicilios(ABC):

    @abstractmethod
    def obtener_menos_pedidos_activos(self) -> Optional[int]:
        """Devuelve el id del domiciliario con menos pedidos activos (EnCamino)."""
        pass

    @abstractmethod
    def crear(self, domicilio: Domicilio) -> Domicilio:
        """Guarda un nuevo domicilio en la base de datos."""
        pass

    @abstractmethod
    def obtener_por_id(self, id_domicilio: int) -> Optional[Domicilio]:
        """Busca un domicilio por su ID."""
        pass

    @abstractmethod
    def listar_por_domiciliario(self, id_domiciliario: int) -> List[Domicilio]:
        """Lista los domicilios asignados a un domiciliario específico."""
        pass

    @abstractmethod
    def actualizar(self, domicilio: Domicilio) -> None:
        """Actualiza el estado de la entrega y el domiciliario asignado."""
        pass
