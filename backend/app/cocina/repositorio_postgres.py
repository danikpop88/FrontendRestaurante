"""
repositorio_postgres.py — Implementación del repositorio de Cocina.
"""

from typing import List, Optional
from app.cocina.repositorio import IRepositorioCocina
from app.pedidos.repositorio_postgres import RepositorioPedidosPostgres
from app.pedidos.modelos import IPedido


class RepositorioCocinaPostgres(IRepositorioCocina):
    def __init__(self, conexion):
        self.conexion = conexion
        self.repo_pedidos = RepositorioPedidosPostgres(conexion)

    def listar_cola(self, tipo_pedido: Optional[str] = None) -> List[IPedido]:
        sql = """
            SELECT id_pedido FROM pedido 
            WHERE estado_pedido IN ('Recibido', 'EnCocina')
        """
        params = []
        if tipo_pedido:
            sql += " AND tipo_pedido = %s"
            params.append(tipo_pedido)

        sql += " ORDER BY fecha ASC"

        pedidos = []
        with self.conexion.cursor() as cur:
            cur.execute(sql, tuple(params))
            filas = cur.fetchall()
            for fila in filas:
                # Reutilizamos la lógica de Fase 5 para traer el pedido completo
                pedido = self.repo_pedidos.obtener_por_id(fila[0])
                if pedido:
                    pedidos.append(pedido)
        return pedidos
