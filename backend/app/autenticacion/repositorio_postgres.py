"""
repositorio_postgres.py — La implementación de IRepositorioUsuarios con PostgreSQL.

PAPEL EN LA ARQUITECTURA: es la ÚNICA pieza del módulo de autenticación que
ejecuta SQL (Artículo 2 de la constitución). Usa psycopg con consultas
parametrizadas: los valores viajan siempre como parámetros (%s con una tupla),
nunca pegados dentro del texto SQL (Artículo 6), que es la defensa contra la
inyección SQL. Aquí no hay reglas de negocio: solo se guarda y se busca.

Toda la jerarquía de usuarios vive en UNA tabla, usuario (5_data_model.md §3.1):
    tipo_cargo vacío (NULL)  -> es un Cliente
    tipo_cargo con valor     -> es un empleado; el valor dice cuál

Qué clase de empleado crear según el tipo_cargo no lo decide este archivo: se
lo entrega main.py (el punto único de ensamblaje) en el diccionario
clases_empleado, por ejemplo {"Mesero": Mesero, ...}. Un tipo_cargo que no esté
en ese diccionario se trata como si el usuario no existiera.
"""

from app.autenticacion.modelos import Cliente, IEmpleado, IUsuario
from app.autenticacion.repositorio import IRepositorioUsuarios

# Columnas que se leen siempre, en este orden (el mismo que usa _a_dominio).
_COLUMNAS = ("id_usuario, nombre, telefono, email, contrasena, "
             "direccion, id_empleado, tipo_cargo, estado")


class RepositorioUsuariosPostgres(IRepositorioUsuarios):

    def __init__(self, conexion, clases_empleado: dict[str, type[IEmpleado]]):
        self._conexion = conexion                   # la conexión de esta petición
        self._clases_empleado = clases_empleado     # tipo_cargo -> clase concreta

    # ----------------------------------------------------------- consultas
    def buscar_por_email(self, email: str) -> IUsuario | None:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT {_COLUMNAS} FROM usuario WHERE email = %s",
                (email,),
            )
            fila = cursor.fetchone()
        return self._a_dominio(fila)

    def buscar_por_id(self, id_usuario: int) -> IUsuario | None:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT {_COLUMNAS} FROM usuario WHERE id_usuario = %s",
                (id_usuario,),
            )
            fila = cursor.fetchone()
        return self._a_dominio(fila)

    # ----------------------------------------------------------- escrituras
    def guardar_cliente(self, cliente: Cliente) -> Cliente:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO usuario (nombre, telefono, email, contrasena, direccion) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id_usuario",
                (cliente.nombre, cliente.telefono, cliente.email,
                 cliente.contrasena, cliente.direccion),
            )
            cliente.id_usuario = cursor.fetchone()[0]
        self._conexion.commit()
        return cliente

    def guardar_empleado(self, empleado: IEmpleado) -> IEmpleado:
        # El id_empleado se asigna al crear la cuenta: el siguiente número libre.
        # La restricción UNIQUE de la base impide que se repita.
        with self._conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO usuario "
                "(nombre, telefono, email, contrasena, id_empleado, tipo_cargo, estado) "
                "VALUES (%s, %s, %s, %s, "
                "(SELECT COALESCE(MAX(id_empleado), 0) + 1 FROM usuario), %s, %s) "
                "RETURNING id_usuario, id_empleado",
                (empleado.nombre, empleado.telefono, empleado.email,
                 empleado.contrasena, empleado.tipo_cargo, empleado.estado),
            )
            empleado.id_usuario, empleado.id_empleado = cursor.fetchone()
        self._conexion.commit()
        return empleado

    def guardar_direccion(self, cliente: Cliente) -> None:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE usuario SET direccion = %s WHERE id_usuario = %s",
                (cliente.direccion, cliente.id_usuario),
            )
        self._conexion.commit()

    # ------------------------------------------------- fila -> clase de dominio
    def _a_dominio(self, fila) -> IUsuario | None:
        """Convierte una fila de la tabla usuario en Cliente o en el empleado que corresponda."""
        if fila is None:
            return None
        (id_usuario, nombre, telefono, email, contrasena,
         direccion, id_empleado, tipo_cargo, estado) = fila
        if tipo_cargo is None:
            return Cliente(id_usuario, nombre, telefono, email, contrasena, direccion)
        clase = self._clases_empleado.get(tipo_cargo)
        if clase is None:
            return None     # cargo sin clase registrada todavía (el Chef, hasta la Fase 7)
        return clase(id_usuario, nombre, telefono, email, contrasena, id_empleado, estado)