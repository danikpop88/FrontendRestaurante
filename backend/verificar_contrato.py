"""
verificar_contrato.py — Verificación de la Fase 9 (herramienta, no es parte de app/).

PAPEL: comprueba dos cosas sin levantar el servidor ni tocar la base de datos:
  1. Las rutas registradas en la API coinciden con la tabla de Contratos §9:
     ninguna falta y ninguna sobra.
  2. Ningún archivo de app/ (salvo main.py y los repositorios) menciona
     'repositorio_postgres' (Plan §5.11).

Cómo correrlo (desde la carpeta backend/, con el entorno virtual activo):
    python verificar_contrato.py
"""

from pathlib import Path

from fastapi.routing import APIRoute

from app.main import app

ESPERADAS = {
    ("POST", "/api/autenticacion/registro"),
    ("POST", "/api/autenticacion/empleados"),
    ("POST", "/api/autenticacion/sesion"),
    ("DELETE", "/api/autenticacion/sesion"),
    ("PUT", "/api/autenticacion/direccion"),
    ("GET", "/api/menu/productos"),
    ("POST", "/api/menu/productos"),
    ("PUT", "/api/menu/productos/{id_producto}"),
    ("PATCH", "/api/menu/productos/{id_producto}/disponibilidad"),
    ("POST", "/api/pedidos/resumen"),
    ("POST", "/api/pedidos"),
    ("GET", "/api/pedidos"),
    ("GET", "/api/pedidos/{id_pedido}"),
    ("PUT", "/api/pedidos/{id_pedido}"),
    ("DELETE", "/api/pedidos/{id_pedido}"),
    ("GET", "/api/cocina/pedidos"),
    ("POST", "/api/cocina/pedidos/{id_pedido}/tomar"),
    ("POST", "/api/cocina/pedidos/{id_pedido}/marcar-listo"),
    ("GET", "/api/notificaciones"),
    ("PATCH", "/api/notificaciones/{id_aviso}"),
    ("GET", "/api/domicilios"),
    ("PATCH", "/api/domicilios/{id_domicilio}/estado-entrega"),
    ("GET", "/api/ventas-pagos"),
    ("GET", "/api/reservas"),
}

RAIZ_APP = Path(__file__).parent / "app"


def rutas_registradas() -> set[tuple[str, str]]:
    encontradas = set()
    for ruta in app.routes:
        if isinstance(ruta, APIRoute):
            for metodo in ruta.methods:
                if metodo not in ("HEAD", "OPTIONS"):
                    encontradas.add((metodo, ruta.path))
    return encontradas


def archivos_con_repositorio_postgres() -> list[str]:
    infractores = []
    for archivo in sorted(RAIZ_APP.rglob("*.py")):
        if archivo == RAIZ_APP / "main.py":
            continue
        if archivo.name == "repositorio_postgres.py":
            continue
        texto = archivo.read_text(encoding="utf-8")
        for numero, linea in enumerate(texto.splitlines(), start=1):
            if "repositorio_postgres" in linea:
                relativo = archivo.relative_to(RAIZ_APP)
                infractores.append(f"  {relativo}:{numero}: {linea.strip()}")
    return infractores


def main() -> None:
    registradas = rutas_registradas()
    faltan = sorted(ESPERADAS - registradas)
    sobran = sorted(registradas - ESPERADAS)

    print("== Rutas contra Contratos §9 ==")
    print(f"Esperadas: {len(ESPERADAS)} | Registradas: {len(registradas)}")
    print("Faltan:", "ninguna" if not faltan else "")
    for metodo, ruta in faltan:
        print(f"  FALTA  {metodo} {ruta}")
    print("Sobran:", "ninguna" if not sobran else "")
    for metodo, ruta in sobran:
        print(f"  SOBRA  {metodo} {ruta}")

    print()
    print("== 'repositorio_postgres' fuera de main.py y de los repositorios ==")
    infractores = archivos_con_repositorio_postgres()
    if infractores:
        print("\n".join(infractores))
    else:
        print("Ninguno.")

    todo_bien = not faltan and not sobran and not infractores
    print()
    print("RESULTADO:", "OK" if todo_bien else "HAY HALLAZGOS")


if __name__ == "__main__":
    main()