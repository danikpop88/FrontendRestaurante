"""
respuestas.py — Cómo se muestra un pedido en las respuestas JSON (Contratos §3).

PAPEL EN LA ARQUITECTURA: reúne la conversión de un pedido de dominio a
diccionario para que TODAS las rutas que devuelven "el pedido" (pedidos y
cocina) muestren exactamente los mismos campos. Así el formato queda escrito
en un solo lugar. No contiene reglas de negocio ni SQL.
"""

from app.pedidos.modelos import DetallePedido, IPedido


def detalle_json(d: DetallePedido) -> dict:
    return {
        "id_producto": d.id_producto,
        "nombre": d.nombre,
        "cantidad": d.cantidad,
        "precio_unitario": float(d.precio_unitario),
        "observaciones_especiales": d.observaciones_especiales,
        "subtotal": float(d.calcular_subtotal()),
    }


def pedido_json(pedido: IPedido) -> dict:
    """El pedido como lo muestran los Contratos §3."""
    return {
        "id_pedido": pedido.id_pedido,
        "tipo_pedido": pedido.obtener_tipo().value,
        "estado_pedido": pedido.obtener_estado(),
        "fecha": pedido.fecha.isoformat(timespec="seconds"),
        "total": float(pedido.total),
        "numero_mesa": getattr(pedido, "numero_mesa", None),
        "direccion": getattr(pedido, "direccion", None),
        "detalle": [detalle_json(d) for d in pedido.detalle],
    }