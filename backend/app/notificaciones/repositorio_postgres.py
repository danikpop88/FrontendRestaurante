"""
repositorio_postgres.py — Implementación del repositorio de Notificaciones.

PAPEL EN LA ARQUITECTURA: capa de datos que interactúa con la tabla 'aviso'
usando psycopg con consultas parametrizadas (Artículo 2 y 6).
"""

from app.notificaciones.repositorio import IRepositorioAvisos


class RepositorioAvisosPostgres(IRepositorioAvisos):

    def __init__(self, conexion):
        self._conexion = conexion

    def listar_por_usuario(
        self, id_usuario: int, leido: bool | None = None
    ) -> list[dict]:
        sql = "SELECT id_aviso, mensaje, fecha, leido FROM aviso WHERE id_usuario = %s"
        parametros = [id_usuario]
        if leido is not None:
            sql += " AND leido = %s"
            parametros.append(leido)
        sql += " ORDER BY fecha DESC"

        with self._conexion.cursor() as cursor:
            cursor.execute(sql, tuple(parametros))
            filas = cursor.fetchall()
        return [
            {
                "id_aviso": f[0],
                "mensaje": f[1],
                "fecha": f[2].isoformat() if f[2] else None,
                "leido": f[3],
            }
            for f in filas
        ]

    def marcar_como_leido(self, id_aviso: int, id_usuario: int) -> bool:
        with self._conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE aviso SET leido = true WHERE id_aviso = %s AND id_usuario = %s",
                (id_aviso, id_usuario),
            )
            modificados = cursor.rowcount
        self._conexion.commit()
        return modificados > 0