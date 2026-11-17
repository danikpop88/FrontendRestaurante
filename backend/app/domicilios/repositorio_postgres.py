"""
repositorio_postgres.py — La implementación real del repositorio con PostgreSQL.

PAPEL EN LA ARQUITECTURA: es la capa de datos del componente "Domicilios".
Usa psycopg con consultas parametrizadas (Artículo 2 y 6 de la constitución)
para evitar inyección SQL. Su trabajo es convertir las filas de la base de
datos a objetos de dominio (Domicilio) y viceversa.
"""

from typing import List, Optional
from app.domicilios.repositorio import IRepositorioDomicilios
from app.domicilios.modelos import Domicilio


class RepositorioDomiciliosPostgres(IRepositorioDomicilios):

    def __init__(self, conexion):
        self.conexion = conexion

    def obtener_menos_pedidos_activos(self) -> Optional[int]:
        """
        Consulta SQL parametrizada para buscar el domiciliario con menos pedidos activos.
        Cuenta los pedidos que están 'EnCamino' para cada domiciliario y ordena de menor a mayor.
        """
        sql = """
            SELECT u.id_usuario, COUNT(p.id_pedido) as pedidos_activos
            FROM usuario u
            LEFT JOIN domicilio d ON u.id_usuario = d.id_domiciliario
            LEFT JOIN pedido p ON d.id_pedido = p.id_pedido AND p.estado_pedido = 'EnCamino'
            WHERE u.tipo_cargo = 'Domiciliario' AND u.estado = true
            GROUP BY u.id_usuario
            ORDER BY pedidos_activos ASC
            LIMIT 1;
        """
        with self.conexion.cursor() as cur:
            cur.execute(sql)
            fila = cur.fetchone()
            if fila:
                return fila[0]
            return None

    def crear(self, domicilio: Domicilio) -> Domicilio:
        """Inserta un domicilio en la base de datos y le asigna el ID generado."""
        sql = """
            INSERT INTO domicilio (id_pedido, id_domiciliario, direccion, estado_entrega, fecha_entrega, motivo_devolucion)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_domicilio;
        """
        with self.conexion.cursor() as cur:
            cur.execute(
                sql,
                (
                    domicilio.pedido.id_pedido,
                    domicilio.id_domiciliario,
                    domicilio.direccion,
                    domicilio.estado_entrega,
                    domicilio.fecha_entrega,
                    domicilio.motivo_devolucion,
                ),
            )
            domicilio.id_domicilio = cur.fetchone()[0]
            self.conexion.commit()
            return domicilio

    def obtener_por_id(self, id_domicilio: int) -> Optional[Domicilio]:
        # TODO: En la T6.3/T6.4 se conectará con IRepositorioPedidos para traer el pedido completo
        # Por ahora dejamos la estructura base del SELECT
        sql = """
            SELECT id_domicilio, id_pedido, id_domiciliario, direccion, estado_entrega, fecha_entrega, motivo_devolucion
            FROM domicilio WHERE id_domicilio = %s;
        """
        with self.conexion.cursor() as cur:
            cur.execute(sql, (id_domicilio,))
            # La reconstrucción completa requiere el PedidoDomicilio (Fase 5).
            # Se completará cuando se integre con el GestorPedidos.
            pass

    def listar_por_domiciliario(self, id_domiciliario: int) -> List[Domicilio]:
        # TODO: Al igual que obtener_por_id, requiere integración con el repositorio de pedidos
        # para reconstruir los objetos de dominio completos.
        pass

    def actualizar(self, domicilio: Domicilio) -> None:
        """Actualiza el estado de la entrega y el domiciliario asignado."""
        sql = """
            UPDATE domicilio 
            SET estado_entrega = %s, fecha_entrega = %s, motivo_devolucion = %s, id_domiciliario = %s
            WHERE id_domicilio = %s;
        """
        with self.conexion.cursor() as cur:
            cur.execute(
                sql,
                (
                    domicilio.estado_entrega,
                    domicilio.fecha_entrega,
                    domicilio.motivo_devolucion,
                    domicilio.id_domiciliario,
                    domicilio.id_domicilio,
                ),
            )
            self.conexion.commit()
