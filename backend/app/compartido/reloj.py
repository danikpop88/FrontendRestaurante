"""
reloj.py — La hora del sistema, inyectable para poder probar los plazos.

PAPEL EN LA ARQUITECTURA: ninguna clase de negocio llama a datetime.now()
directamente. Reciben un IReloj y le preguntan la hora. Esto aplica la
inversión de dependencias (Artículo 5 de la constitución): el código depende
de la abstracción IReloj, no de una implementación concreta.

    IReloj        -> clase abstracta (ABC): promete un método ahora().
    RelojSistema  -> la hora real; es el que arma main.py en producción.
    RelojFalso    -> un reloj de mentira al que se le puede adelantar la hora;
                     lo usan las pruebas.

Quién lo usa: las sesiones de 30 minutos (seguridad.py, RNF-03) y, más
adelante, la ventana de 5 minutos de los pedidos (RN-01). Con RelojFalso se
comprueba que una sesión vence a los 30 minutos sin esperar 30 minutos.

Las horas son "ingenuas" (sin zona horaria), igual que las columnas TIMESTAMP
de la base de datos.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class IReloj(ABC):
    """Contrato de un reloj: cualquier reloj debe saber decir la hora actual."""

    @abstractmethod
    def ahora(self) -> datetime:
        """Devuelve la fecha y hora actuales."""


class RelojSistema(IReloj):
    """El reloj real: devuelve la hora del computador donde corre la API."""

    def ahora(self) -> datetime:
        return datetime.now()


class RelojFalso(IReloj):
    """Reloj para pruebas: la hora no avanza sola, solo cuando se le ordena."""

    def __init__(self, inicio: datetime | None = None):
        # Si no se indica una hora de inicio, arranca en la hora actual.
        self._hora = inicio if inicio is not None else datetime.now()

    def ahora(self) -> datetime:
        return self._hora

    def adelantar(self, minutos: int) -> None:
        """Mueve la hora hacia adelante, por ejemplo adelantar(31)."""
        self._hora = self._hora + timedelta(minutes=minutos)