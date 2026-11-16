"""
excepciones.py — Los errores de negocio de la API.

PAPEL EN LA ARQUITECTURA: la capa de negocio (los servicios) no conoce HTTP.
Cuando algo no se cumple, lanza una de estas excepciones con un mensaje claro
en español. La capa de rutas (los manejadores registrados en main.py) las
traduce a su código HTTP (Plan §5.10, Contratos §0):

    NoAutenticadoError -> 401  (sin sesión, credenciales inválidas, sesión expirada)
    SinPermisoError    -> 403  (rol sin permiso: RN-09, RN-10)
    NoEncontradoError  -> 404  (pedido, producto o usuario inexistente)
    ReglaNegocioError  -> 409  (regla violada: RN-01, RN-04, RN-05, RN-07, RN-08,
                                o dato ya registrado, como un email repetido)

Cómo se usan: raise SinPermisoError("Solo el administrador puede modificar el menú.")
El mensaje es el que verá el usuario, por eso nunca incluye detalles técnicos
(Artículo 7 de la constitución).
"""


class NoAutenticadoError(Exception):
    """El usuario no tiene sesión válida (401)."""


class SinPermisoError(Exception):
    """El usuario tiene sesión, pero su rol no permite la acción (403)."""


class NoEncontradoError(Exception):
    """El recurso pedido no existe (404)."""


class ReglaNegocioError(Exception):
    """Se violó una regla de negocio o el dato ya está registrado (409)."""