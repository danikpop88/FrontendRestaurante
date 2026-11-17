"""
repositorio_postgres.py — Implementación del repositorio de Notificaciones.

PAPEL EN LA ARQUITECTURA: capa de datos que interactúa con la tabla 'aviso'
usando psycopg con consultas parametrizadas (Artículo 2 y 6).
"""

from typing import List, Optional
from app.notificaciones.repositorio import IRepositorioAvisos


class RepositorioAvisosPostgres(IRepositorioAvisos):
    def __init__(self, conexion):
        self.conexion = conexion

    def listar_por_usuario(
        self, id_usuario: int, leido: Optional[bool] = None
    ) -> List[dict]:
        sql = "SELECT id_aviso, mensaje, fecha, leido FROM aviso WHERE id_usuario = %s"
        params = [id_usuario]

        if leido is not None:
            sql += " AND leido = %s"
            params.append(leido)

        sql += " ORDER BY fecha DESC"

        resultados = []
        with self.conexion.cursor() as cur:
            cur.execute(sql, tuple(params))
            for fila in cur.fetchall():
                resultados.append(
                    {
                        "id_aviso": fila[0],
                        "mensaje": fila[1],
                        "fecha": fila[2].isoformat() if fila[2] else None,
                        "leido": fila[3],
                    }
                )
        return resultados

    def marcar_como_leido(self, id_aviso: int, id_usuario: int) -> None:
        sql = "UPDATE aviso SET leido = true WHERE id_aviso = %s AND id_usuario = %s"
        with self.conexion.cursor() as cur:
            cur.execute(sql, (id_aviso, id_usuario))
            self.conexion.commit()
