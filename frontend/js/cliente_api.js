// =====================================================================
// frontend/js/cliente_api.js
// Cliente de la API: la ÚNICA pieza del front que usa fetch (C4 nivel 3).
// Arma la petición, añade el token de sesión y traduce cada respuesta a
// la forma { ok, datos, errores, mensaje } según 6_contracts.md §12.
// Las vistas nunca ven verbos HTTP, rutas ni códigos de estado.
// =====================================================================

const ClienteApi = (() => {
  const URL_BASE = "http://localhost:8000";
  const CLAVE_SESION = "mesa_abuela_sesion";

  let alExpirarSesion = null; // función que registra autenticacion.js

  // ---------- Sesión (solo el token y los datos del usuario) ----------
  function leerSesion() {
    try {
      const texto = sessionStorage.getItem(CLAVE_SESION);
      return texto ? JSON.parse(texto) : null;
    } catch (e) {
      return null;
    }
  }

  function guardarSesion(sesion) {
    try {
      sessionStorage.setItem(CLAVE_SESION, JSON.stringify(sesion));
    } catch (e) { /* sin almacenamiento: la sesión vive solo en esta pestaña */ }
  }

  function borrarSesion() {
    try {
      sessionStorage.removeItem(CLAVE_SESION);
    } catch (e) { /* nada que borrar */ }
  }

  // ---------- Traducción de respuestas (tabla de 6_contracts.md §12) ----------
  function resultado(ok, datos, errores, mensaje) {
    return { ok: ok, datos: datos, errores: errores || [], mensaje: mensaje || "" };
  }

  function traducir(estado, cuerpo, habiaSesion) {
    const mensajeApi = cuerpo && cuerpo.mensaje ? cuerpo.mensaje : "";

    if (estado === 200 || estado === 201) {
      // Las listas llegan como { total, datos: [...] }: la vista recibe la lista.
            const datos = cuerpo && Array.isArray(cuerpo.datos) && cuerpo.total_ventas === undefined ? cuerpo.datos : cuerpo;
      return resultado(true, datos, [], mensajeApi);
    }
    if (estado === 422) {
      const errores = cuerpo && Array.isArray(cuerpo.errores) && cuerpo.errores.length
        ? cuerpo.errores
        : [mensajeApi || "Revise los datos ingresados."];
      return resultado(false, null, errores, errores[0]);
    }
    if (estado === 409 || estado === 404) {
      return resultado(false, null, [], mensajeApi || "No se pudo completar la acción.");
    }
    if (estado === 401) {
      borrarSesion();
      const mensaje = habiaSesion ? "Su sesión expiró. Ingrese de nuevo." : (mensajeApi || "Credenciales inválidas.");
      if (habiaSesion && alExpirarSesion) alExpirarSesion();
      return resultado(false, null, [], mensaje);
    }
    if (estado === 403) {
      return resultado(false, null, [], "No tiene permiso para hacer esto.");
    }
    return resultado(false, null, [], "Ocurrió un error, intente de nuevo.");
  }

  // ---------- La única función que usa fetch ----------
  async function solicitar(verbo, ruta, cuerpo, consulta) {
    const sesion = leerSesion();
    const cabeceras = { "Content-Type": "application/json" };
    if (sesion && sesion.token) cabeceras["Authorization"] = "Bearer " + sesion.token;

    let url = URL_BASE + ruta;
    if (consulta) {
      const params = new URLSearchParams();
      Object.keys(consulta).forEach((k) => {
        if (consulta[k] !== undefined && consulta[k] !== null && consulta[k] !== "") {
          params.append(k, consulta[k]);
        }
      });
      const texto = params.toString();
      if (texto) url += "?" + texto;
    }

    let respuesta;
    try {
      respuesta = await fetch(url, {
        method: verbo,
        headers: cabeceras,
        body: cuerpo !== undefined && cuerpo !== null ? JSON.stringify(cuerpo) : undefined,
      });
    } catch (e) {
      // La API no respondió: no se inventa ningún código.
      const r = resultado(false, null, [], "El servicio no está disponible.");
      r.sinServicio = true;
      return r;
    }

    let json = null;
    try {
      json = await respuesta.json();
    } catch (e) {
      json = null;
    }
    return traducir(respuesta.status, json, !!(sesion && sesion.token));
  }

  // ---------- Autenticación (RF-01, RF-06) ----------
  async function iniciarSesion(email, contrasena) {
    const r = await solicitar("POST", "/api/autenticacion/sesion", { email: email, contrasena: contrasena });
    if (r.ok) {
      guardarSesion({ token: r.datos.token, rol: r.datos.rol, usuario: r.datos.usuario });
    }
    return r;
  }

  async function cerrarSesion() {
    const r = await solicitar("DELETE", "/api/autenticacion/sesion");
    borrarSesion(); // aunque la API no responda, la sesión local se cierra
    return r;
  }

  // ---------- Métodos por vista (los nombres no mencionan HTTP) ----------
  return {
    // sesión local
    sesionActual: leerSesion,
    haySesion: () => !!(leerSesion() && leerSesion().token),
    alExpirarSesion: (funcion) => { alExpirarSesion = funcion; },

    // autenticación
    iniciarSesion: iniciarSesion,
    cerrarSesion: cerrarSesion,
    registrarCliente: (datos) => solicitar("POST", "/api/autenticacion/registro", datos),
    crearEmpleado: (datos) => solicitar("POST", "/api/autenticacion/empleados", datos),
    guardarDireccion: (direccion) => solicitar("PUT", "/api/autenticacion/direccion", { direccion: direccion }),

    // menú
    listarMenu: (categoria) => solicitar("GET", "/api/menu/productos", null, { categoria: categoria }),
    crearProducto: (datos) => solicitar("POST", "/api/menu/productos", datos),
    editarProducto: (id, datos) => solicitar("PUT", "/api/menu/productos/" + id, datos),
    cambiarDisponibilidad: (id, disponible) =>
      solicitar("PATCH", "/api/menu/productos/" + id + "/disponibilidad", { disponible: disponible }),

    // pedidos
    resumenPedido: (datos) => solicitar("POST", "/api/pedidos/resumen", datos),
    crearPedido: (datos) => solicitar("POST", "/api/pedidos", datos),
    listarPedidos: (estado) => solicitar("GET", "/api/pedidos", null, { estado_pedido: estado }),
    obtenerPedido: (id) => solicitar("GET", "/api/pedidos/" + id),
    modificarPedido: (id, datos) => solicitar("PUT", "/api/pedidos/" + id, datos),
    cancelarPedido: (id) => solicitar("DELETE", "/api/pedidos/" + id),

    // cocina
    colaCocina: (tipoPedido) => solicitar("GET", "/api/cocina/pedidos", null, { tipo_pedido: tipoPedido }),
    tomarPedido: (id) => solicitar("POST", "/api/cocina/pedidos/" + id + "/tomar"),
    marcarListo: (id) => solicitar("POST", "/api/cocina/pedidos/" + id + "/marcar-listo"),

    // domicilios
    listarDomicilios: () => solicitar("GET", "/api/domicilios"),
    cerrarEntrega: (id, estadoEntrega, motivo) => {
      const cuerpo = { estado_entrega: estadoEntrega };
      if (motivo) cuerpo.motivo_devolucion = motivo;
      return solicitar("PATCH", "/api/domicilios/" + id + "/estado-entrega", cuerpo);
    },

    // notificaciones (avisos simulados)
    listarAvisos: (leido) => solicitar("GET", "/api/notificaciones", null, { leido: leido }),
    marcarAvisoLeido: (id) => solicitar("PATCH", "/api/notificaciones/" + id, { leido: true }),

    // ventas y reservas (administrador)
    consultarVentas: (desde, hasta) => solicitar("GET", "/api/ventas-pagos", null, { desde: desde, hasta: hasta }),
    listarReservas: () => solicitar("GET", "/api/reservas"),
  };
})();