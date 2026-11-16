"""
conexion.py — Una conexión a PostgreSQL por petición.

PAPEL EN LA ARQUITECTURA: solo la API habla con la base de datos (Artículo 2
de la constitución), y dentro de la API únicamente los repositorios ejecutan
SQL. Este archivo es el que abre la conexión y la entrega; no contiene
consultas ni reglas de negocio.

Cómo se usa: FastAPI llama a obtener_conexion() cuando llega una petición que
la necesita, entrega la conexión a quien la pide y, al terminar la petición,
vuelve a esta función para cerrarla. Importante: la conexión solo se abre
cuando llega una petición, por eso la API puede arrancar aunque PostgreSQL
esté apagado.

Transacciones: psycopg 3 abre una transacción implícita con la primera
consulta. Cuando una operación escribe en varias tablas (crear un pedido con
su detalle, registrar el cobro), el repositorio llama a conexion.commit() al
final para guardarla toda junta. Si algo falla antes del commit, la conexión se
cierra y PostgreSQL descarta los cambios pendientes (rollback).
"""

import psycopg

from app import config


def obtener_conexion():
    """Abre la conexión, la entrega y garantiza que se cierre al terminar."""
    conexion = psycopg.connect(
        host=config.DB_HOST,
        port=config.DB_PUERTO,
        dbname=config.DB_NOMBRE,
        user=config.DB_USUARIO,
        password=config.DB_CLAVE,
    )
    try:
        yield conexion      # aquí la usa la ruta y el repositorio
    finally:
        conexion.close()    # se ejecuta siempre, haya o no error