"""
seguridad.py — Claves con hash, sesiones en memoria y control de rol.

PAPEL EN LA ARQUITECTURA: reúne lo que protege a la API (Artículo 6 de la
constitución). Tiene tres piezas:

  1. hashear_clave / verificar_clave: las claves se guardan siempre con hash
     scrypt y una sal propia por usuario, nunca en texto plano (RNF-01). La
     longitud mínima de 12 caracteres se valida en el servicio, ANTES de
     calcular el hash.
  2. GestorSesiones: al iniciar sesión se crea un token aleatorio que se guarda
     EN MEMORIA junto con su último acceso. Si pasan 30 minutos sin actividad,
     la sesión vence (RNF-03). Si el servidor se reinicia, las sesiones se
     pierden y hay que iniciar sesión de nuevo. Recibe un IReloj para poder
     probar el vencimiento sin esperar 30 minutos reales.
  3. requiere_rol(...): dependencia de FastAPI que las rutas usan para exigir
     sesión y rol. Rechaza al que no tiene sesión (NoAutenticadoError, 401) y
     al que tiene un rol que no corresponde (SinPermisoError, 403).

Quién guarda el GestorSesiones: lo crea main.py (el único punto de ensamblaje)
y lo deja en app.state.sesiones; requiere_rol lo toma de ahí.
"""

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import Header, Request

from app import config
from app.compartido.excepciones import NoAutenticadoError, SinPermisoError
from app.compartido.reloj import IReloj


# =====================================================================
# 1. HASH DE CLAVES (scrypt con sal por usuario)
# =====================================================================

# Parámetros de scrypt: costo de CPU/memoria (n), tamaño de bloque (r) y
# paralelismo (p). Son los valores habituales recomendados para claves.
_N = 2 ** 14
_R = 8
_P = 1


def hashear_clave(clave: str) -> str:
    """
    Devuelve el hash de la clave listo para guardar en usuario.contrasena.
    Formato: "<sal en hexadecimal>$<hash en hexadecimal>".
    Cada llamada usa una sal nueva, así dos usuarios con la misma clave
    tienen hashes distintos.
    """
    sal = os.urandom(16)
    derivado = hashlib.scrypt(clave.encode("utf-8"), salt=sal, n=_N, r=_R, p=_P)
    return sal.hex() + "$" + derivado.hex()


def verificar_clave(clave: str, guardado: str) -> bool:
    """
    Comprueba si la clave escrita corresponde al hash guardado.
    Devuelve False (nunca lanza error) si el valor guardado no tiene el
    formato esperado, por ejemplo el marcador PENDIENTE_FASE_2.
    """
    try:
        sal_hex, hash_hex = guardado.split("$")
        sal = bytes.fromhex(sal_hex)
        esperado = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    derivado = hashlib.scrypt(clave.encode("utf-8"), salt=sal, n=_N, r=_R, p=_P)
    # compare_digest compara sin revelar, por el tiempo que tarda, en qué byte falló.
    return hmac.compare_digest(derivado, esperado)


# =====================================================================
# 2. SESIONES EN MEMORIA (vencen a los 30 minutos de inactividad)
# =====================================================================

@dataclass
class Sesion:
    """Lo que la API recuerda de una sesión abierta."""
    id_usuario: int
    rol: str                  # tipo_cargo del usuario; "Cliente" si no tiene
    ultimo_acceso: datetime


class GestorSesiones:
    """Guarda las sesiones abiertas: token -> Sesion."""

    def __init__(self, reloj: IReloj, minutos_vencimiento: int = config.MINUTOS_SESION):
        self._reloj = reloj
        self._vencimiento = timedelta(minutes=minutos_vencimiento)
        self._sesiones: dict[str, Sesion] = {}

    def crear(self, id_usuario: int, rol: str) -> str:
        """Abre una sesión y devuelve su token."""
        token = secrets.token_urlsafe(32)
        self._sesiones[token] = Sesion(id_usuario, rol, self._reloj.ahora())
        return token

    def obtener(self, token: str) -> Sesion:
        """
        Devuelve la sesión del token y renueva su último acceso.
        Lanza NoAutenticadoError si el token no existe o la sesión venció.
        """
        sesion = self._sesiones.get(token)
        if sesion is None:
            raise NoAutenticadoError("Debe iniciar sesión para continuar.")
        ahora = self._reloj.ahora()
        if ahora - sesion.ultimo_acceso >= self._vencimiento:
            del self._sesiones[token]           # la sesión vencida se descarta
            raise NoAutenticadoError("Su sesión expiró. Inicie sesión de nuevo.")
        sesion.ultimo_acceso = ahora            # cada petición renueva el plazo
        return sesion

    def cerrar(self, token: str) -> None:
        """Termina la sesión. Si el token no existe, no hace nada."""
        self._sesiones.pop(token, None)


# =====================================================================
# 3. CONTROL DE ROL (dependencia de FastAPI)
# =====================================================================

def extraer_token(authorization: str | None) -> str:
    """Saca el token de la cabecera 'Authorization: Bearer <token>'."""
    if authorization is None or not authorization.startswith("Bearer "):
        raise NoAutenticadoError("Debe iniciar sesión para continuar.")
    return authorization[len("Bearer "):].strip()


def requiere_rol(*roles_permitidos: str):
    """
    Crea la dependencia que una ruta usa para exigir sesión y rol.
    Ejemplo en una ruta:  sesion = Depends(requiere_rol("Administrador"))
    Sin roles (requiere_rol()) basta con tener una sesión válida.
    Devuelve la Sesion, así la ruta sabe quién hace la petición.
    """
    def dependencia(request: Request, authorization: str | None = Header(default=None)) -> Sesion:
        token = extraer_token(authorization)
        sesion = request.app.state.sesiones.obtener(token)
        if roles_permitidos and sesion.rol not in roles_permitidos:
            raise SinPermisoError("No tiene permiso para realizar esta acción.")
        return sesion
    return dependencia