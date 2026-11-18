"""
verificar_contrato.py — Verificación de la Fase 9 (herramienta, no es parte de app/).

PAPEL: comprueba tres cosas sin levantar el servidor ni tocar la base de datos:
  1. Las rutas que publica la API (las mismas de /docs) coinciden con la tabla
     de Contratos §9: ninguna falta y ninguna sobra.
  2. Ningún archivo de app/ (salvo main.py y los repositorios) IMPORTA
     'repositorio_postgres' (Plan §5.11).
  3. Ninguna ruta ni servicio abre conexiones o cursores (Artículo 2): solo los
     repositorios hablan con la base de datos.

Cómo correrlo (desde la carpeta backend/, con el entorno virtual activo):
    python verificar_contrato.py
"""

from pathlib import Path

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

METODOS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
RAIZ_APP = Path(__file__).parent / "app"


def rutas_publicadas() -> set[tuple[str, str]]:
    """Las rutas del esquema OpenAPI: exactamente lo que muestra /docs."""
    encontradas = set()
    for ruta, operaciones in app.openapi()["paths"].items():
        for metodo in operaciones:
            if metodo.upper() in METODOS:
                encontradas.add((metodo.upper(), ruta))
    return encontradas


def _archivos_de_app():
    for archivo in sorted(RAIZ_APP.rglob("*.py")):
        yield archivo, archivo.read_text(encoding="utf-8").splitlines()


def imports_de_repositorio_postgres() -> list[str]:
    infractores = []
    for archivo, lineas in _archivos_de_app():
        if archivo == RAIZ_APP / "main.py" or archivo.name == "repositorio_postgres.py":
            continue
        for numero, linea in enumerate(lineas, start=1):
            texto = linea.strip()
            if "repositorio_postgres" in texto and "import" in texto \
                    and not texto.startswith("#"):
                infractores.append(f"  {archivo.relative_to(RAIZ_APP)}:{numero}: {texto}")
    return infractores


def acceso_a_bd_en_rutas_o_servicios() -> list[str]:
    """Rutas y servicios no deben abrir conexiones ni cursores."""
    infractores = []
    for archivo, lineas in _archivos_de_app():
        if not (archivo.name.startswith("rutas") or archivo.name.startswith("servicio")):
            continue
        if "integraciones" in archivo.parts:      # ServicioPush(conexion): Plan §5.11
            continue
        for numero, linea in enumerate(lineas, start=1):
            texto = linea.strip()
            if texto.startswith("#"):
                continue
            if "obtener_conexion" in texto or ".cursor(" in texto or "import psycopg" in texto:
                infractores.append(f"  {archivo.relative_to(RAIZ_APP)}:{numero}: {texto}")
    return infractores


def main() -> None:
    publicadas = rutas_publicadas()
    faltan = sorted(ESPERADAS - publicadas)
    sobran = sorted(publicadas - ESPERADAS)

    print("== Rutas contra Contratos §9 ==")
    print(f"Esperadas: {len(ESPERADAS)} | Publicadas: {len(publicadas)}")
    for metodo, ruta in faltan:
        print(f"  FALTA  {metodo} {ruta}")
    for metodo, ruta in sobran:
        print(f"  SOBRA  {metodo} {ruta}")
    if not faltan and not sobran:
        print("Coinciden: ninguna falta y ninguna sobra.")

    print()
    print("== Imports de 'repositorio_postgres' fuera de main.py y de los repositorios ==")
    infractores = imports_de_repositorio_postgres()
    print("\n".join(infractores) if infractores else "Ninguno.")

    print()
    print("== Conexiones o cursores dentro de rutas y servicios ==")
    accesos = acceso_a_bd_en_rutas_o_servicios()
    print("\n".join(accesos) if accesos else "Ninguno.")

    todo_bien = not faltan and not sobran and not infractores and not accesos
    print()
    print("RESULTADO:", "OK" if todo_bien else "HAY HALLAZGOS")


if __name__ == "__main__":
    main()