"""
config.py — Configuración de la API (variables de entorno).

PAPEL EN LA ARQUITECTURA: es el único archivo que lee el entorno del sistema.
Los demás módulos importan de aquí lo que necesiten (conexión a la base,
origen permitido del front, plazo de la sesión) y nunca leen os.environ por
su cuenta. Así, cambiar de base de datos o de puerto no obliga a tocar el
código de negocio: solo se cambia una variable.

Una variable de entorno es un valor que se le da al programa desde fuera
(la terminal) antes de ejecutarlo. Ejemplo en PowerShell:
    $env:DB_CLAVE = "mi_clave"
Las pruebas usan la base mesa_abuela_test definiendo DB_NOMBRE.
"""

import os

# --- Conexión a PostgreSQL (puerto 5432 y bases de la constitución) ---------
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PUERTO = int(os.environ.get("DB_PUERTO", "5432"))
DB_NOMBRE = os.environ.get("DB_NOMBRE", "mesa_abuela")      # pruebas: mesa_abuela_test
DB_USUARIO = os.environ.get("DB_USUARIO", "postgres")
DB_CLAVE = os.environ.get("DB_CLAVE", "")                   # sin valor por defecto a propósito

# --- CORS: el backend permite únicamente el origen del front (puerto 5500) --
ORIGEN_FRONT = os.environ.get("ORIGEN_FRONT", "http://localhost:5500")

# --- Plazo de la sesión (RNF-03): 30 minutos de inactividad -----------------
MINUTOS_SESION = 30