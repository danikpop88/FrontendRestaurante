"""
test_nucleo.py — Pruebas del núcleo compartido (Fase 1).

PAPEL EN LA ARQUITECTURA: comprueba, sin base de datos, las piezas que usarán
todos los módulos: el hash de claves, el reloj, las sesiones de 30 minutos
(RNF-03), la traducción de cada excepción a su código HTTP (Plan §5.10) y el
control de rol. Es la prueba de que las reglas de seguridad se cumplen y de
qué pasa cuando se violan (Artículo 3 y Artículo 7 de la constitución).

Cómo se ejecuta (desde la carpeta backend/, con el entorno virtual activo):
    python -m pytest pruebas -v
"""

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from app.compartido.excepciones import (
    NoAutenticadoError,
    NoEncontradoError,
    ReglaNegocioError,
    SinPermisoError,
)
from app.compartido.reloj import IReloj, RelojFalso
from app.compartido.seguridad import (
    GestorSesiones,
    hashear_clave,
    requiere_rol,
    verificar_clave,
)
from app.main import app

CLAVE = "UnaClaveSegura123"


# =====================================================================
# 1. HASH DE CLAVES
# =====================================================================

def test_el_hash_nunca_coincide_con_la_clave_en_texto_plano():
    guardado = hashear_clave(CLAVE)
    assert guardado != CLAVE
    assert CLAVE not in guardado


def test_verificar_clave_acepta_la_correcta_y_rechaza_la_incorrecta():
    guardado = hashear_clave(CLAVE)
    assert verificar_clave(CLAVE, guardado) is True
    assert verificar_clave("OtraClaveDistinta1", guardado) is False


def test_la_misma_clave_genera_hashes_distintos_por_la_sal():
    assert hashear_clave(CLAVE) != hashear_clave(CLAVE)


def test_un_valor_guardado_sin_formato_de_hash_no_permite_entrar():
    # Es el caso del marcador PENDIENTE_FASE_2 de datos_ejemplo.sql.
    assert verificar_clave(CLAVE, "PENDIENTE_FASE_2") is False


# =====================================================================
# 2. RELOJ
# =====================================================================

def test_el_reloj_falso_solo_avanza_cuando_se_le_ordena():
    reloj = RelojFalso()
    inicio = reloj.ahora()
    assert reloj.ahora() == inicio          # no avanza solo
    reloj.adelantar(31)
    assert (reloj.ahora() - inicio).total_seconds() == 31 * 60


def test_ireloj_es_abstracta_y_no_se_puede_instanciar():
    with pytest.raises(TypeError):
        IReloj()


# =====================================================================
# 3. SESIONES (vencen a los 30 minutos de inactividad)
# =====================================================================

def test_la_sesion_vence_a_los_30_minutos():
    reloj = RelojFalso()
    sesiones = GestorSesiones(reloj)
    token = sesiones.crear(1, "Cliente")
    reloj.adelantar(30)
    with pytest.raises(NoAutenticadoError):
        sesiones.obtener(token)
    # Una vez vencida se descarta: no revive aunque el reloj no avance.
    with pytest.raises(NoAutenticadoError):
        sesiones.obtener(token)


def test_la_sesion_sigue_valida_a_los_29_minutos():
    reloj = RelojFalso()
    sesiones = GestorSesiones(reloj)
    token = sesiones.crear(1, "Cliente")
    reloj.adelantar(29)
    assert sesiones.obtener(token).id_usuario == 1


def test_cada_peticion_renueva_el_plazo_de_inactividad():
    reloj = RelojFalso()
    sesiones = GestorSesiones(reloj)
    token = sesiones.crear(1, "Cliente")
    reloj.adelantar(20)
    sesiones.obtener(token)                 # actividad: renueva el último acceso
    reloj.adelantar(20)                     # 40 minutos en total, 20 desde la actividad
    assert sesiones.obtener(token).id_usuario == 1


def test_un_token_que_no_existe_no_autentica():
    sesiones = GestorSesiones(RelojFalso())
    with pytest.raises(NoAutenticadoError):
        sesiones.obtener("token-inventado")


def test_cerrar_la_sesion_invalida_el_token():
    sesiones = GestorSesiones(RelojFalso())
    token = sesiones.crear(1, "Cliente")
    sesiones.cerrar(token)
    with pytest.raises(NoAutenticadoError):
        sesiones.obtener(token)


# =====================================================================
# 4. CADA EXCEPCIÓN PRODUCE SU CÓDIGO HTTP
#    Se agregan rutas de prueba a la aplicación real; así se comprueban los
#    manejadores de main.py tal como funcionan en producción.
# =====================================================================

cliente = TestClient(app, raise_server_exceptions=False)

CASOS = {
    401: NoAutenticadoError("Debe iniciar sesión para continuar."),
    403: SinPermisoError("No tiene permiso para realizar esta acción."),
    404: NoEncontradoError("El recurso no existe."),
    409: ReglaNegocioError("La regla de negocio no se cumple."),
}


def _ruta_que_lanza(excepcion):
    def ruta():
        raise excepcion
    return ruta


for _codigo, _excepcion in CASOS.items():
    app.add_api_route(f"/prueba/error/{_codigo}", _ruta_que_lanza(_excepcion))


@pytest.mark.parametrize("codigo", [401, 403, 404, 409])
def test_cada_excepcion_produce_su_codigo_con_la_envoltura_de_error(codigo):
    respuesta = cliente.get(f"/prueba/error/{codigo}")
    assert respuesta.status_code == codigo
    assert respuesta.json() == {
        "estado": codigo,
        "mensaje": str(CASOS[codigo]),
        "errores": [],
    }


def test_un_error_inesperado_da_500_sin_detalles_internos():
    def ruta_que_falla():
        raise RuntimeError("detalle interno que el usuario no debe ver")

    app.add_api_route("/prueba/error/inesperado", ruta_que_falla)
    respuesta = cliente.get("/prueba/error/inesperado")
    assert respuesta.status_code == 500
    assert "detalle interno" not in respuesta.text
    assert respuesta.json()["estado"] == 500


# =====================================================================
# 5. CONTROL DE ROL (requiere_rol)
# =====================================================================

@app.get("/prueba/solo-administrador")
def solo_administrador(sesion=Depends(requiere_rol("Administrador"))):
    return {"id_usuario": sesion.id_usuario}


@pytest.fixture
def sesiones():
    """Cambia, solo durante la prueba, el gestor de sesiones por uno con reloj falso."""
    original = app.state.sesiones           # se guarda el gestor real de main.py
    gestor = GestorSesiones(RelojFalso())
    app.state.sesiones = gestor
    yield gestor                            # aquí corre la prueba
    app.state.sesiones = original           # al terminar, se devuelve el real


def test_sin_cabecera_de_sesion_responde_401(sesiones):
    assert cliente.get("/prueba/solo-administrador").status_code == 401


def test_con_un_token_invalido_responde_401(sesiones):
    respuesta = cliente.get(
        "/prueba/solo-administrador", headers={"Authorization": "Bearer token-falso"}
    )
    assert respuesta.status_code == 401


def test_con_un_rol_que_no_corresponde_responde_403(sesiones):
    token = sesiones.crear(7, "Mesero")
    respuesta = cliente.get(
        "/prueba/solo-administrador", headers={"Authorization": f"Bearer {token}"}
    )
    assert respuesta.status_code == 403


def test_con_el_rol_correcto_deja_pasar(sesiones):
    token = sesiones.crear(1, "Administrador")
    respuesta = cliente.get(
        "/prueba/solo-administrador", headers={"Authorization": f"Bearer {token}"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {"id_usuario": 1}