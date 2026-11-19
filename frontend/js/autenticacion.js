// =====================================================================
// frontend/js/autenticacion.js
// Sesión y pantallas según el rol (login, registro, guardia por rol,
// cerrar sesión) + ayudas de pantalla (avisos, mensajes, estilos).
// Solo habla con la API a través de ClienteApi.
// =====================================================================

const RAIZ = new URL("../", document.currentScript.src).href;

const Pantalla = (() => {
  const CSS = `
.v-aviso{position:fixed;left:50%;bottom:20px;transform:translateX(-50%);max-width:380px;padding:12px 18px;border-radius:12px;color:#fff;font:600 15px Karla,sans-serif;white-space:pre-line;z-index:3000;box-shadow:0 4px 12px rgba(0,0,0,.3)}
.v-aviso.ok{background:#2DB98B}.v-aviso.error{background:#C0392B}
.v-banner{position:fixed;top:0;left:0;right:0;background:#C0392B;color:#fff;padding:10px 16px;font:600 15px Karla,sans-serif;text-align:center;z-index:2000}
.v-avisos{position:fixed;top:16px;left:50%;transform:translateX(-50%);z-index:3000;display:flex;flex-direction:column;gap:10px;width:300px}
.v-pedido-listo{background:#F9C22E;border:2px solid #000;border-radius:33px;padding:16px;text-align:center;font:700 16px Karla,sans-serif;cursor:pointer;box-shadow:0 4px 10px rgba(0,0,0,.2)}
.v-tarjeta{background:#fff;border:1px solid #D9D9D9;border-radius:12px;padding:12px 14px;margin-bottom:12px;font:16px Inter,sans-serif;color:#1E1E1E;box-sizing:border-box}
.v-boton{display:inline-block;background:#F4CE14;color:#000;border:none;border-radius:16px;padding:8px 16px;font:700 15px Karla,sans-serif;cursor:pointer;margin:6px 6px 0 0;text-decoration:none}
.v-boton.gris{background:#808F85;color:#fff}.v-boton.rojo{background:#C0392B;color:#fff}
.v-vacio{padding:20px;text-align:center;color:#495E57;font:600 16px Karla,sans-serif}
.v-mensajes{color:#C0392B;font:600 14px Karla,sans-serif;width:100%}
.v-select{width:100%;padding:10px 12px;border:1px solid #D9D9D9;border-radius:8px;font:15px Inter,sans-serif;background:#fff;box-sizing:border-box}
.v-tabla{width:100%;border-collapse:collapse;background:#fff;font:14px Karla,sans-serif}
.v-tabla th,.v-tabla td{border:1px solid #D9D9D9;padding:8px;text-align:center}.v-tabla th{background:#EDEFEE}
.sel{outline:3px solid #F4CE14}`;

  const estiloBase = document.createElement("style");
  estiloBase.textContent = CSS;
  document.head.appendChild(estiloBase);

  function esc(t) {
    return String(t === null || t === undefined ? "" : t).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
  function dinero(n) {
    return "$" + Number(n || 0).toLocaleString("es-CO", { maximumFractionDigits: 0 });
  }
  function hora(iso) {
    return new Date(iso).toLocaleTimeString("es-CO", { hour: "numeric", minute: "2-digit" });
  }
  function fechaHora(iso) {
    return new Date(iso).toLocaleString("es-CO", { day: "2-digit", month: "2-digit", year: "2-digit", hour: "numeric", minute: "2-digit" });
  }
  function estilo(css) {
    const s = document.createElement("style");
    s.textContent = css;
    document.head.appendChild(s);
  }
  function aviso(texto, tipo) {
    const a = document.createElement("div");
    a.className = "v-aviso " + (tipo || "ok");
    a.textContent = texto;
    document.body.appendChild(a);
    setTimeout(() => a.remove(), 4500);
  }
  // Muestra u oculta el aviso "servicio no disponible". Devuelve true si la API respondió.
  function servicio(r) {
    const previo = document.getElementById("v-banner");
    if (r && r.sinServicio) {
      if (!previo) {
        const b = document.createElement("div");
        b.id = "v-banner";
        b.className = "v-banner";
        b.textContent = "El servicio no está disponible.";
        document.body.appendChild(b);
      }
      return false;
    }
    if (previo) previo.remove();
    return true;
  }
  function limpiar() {
    const c = document.getElementById("mensajes");
    if (c) c.innerHTML = "";
  }
  // Acepta un resultado de ClienteApi (o un objeto { errores: [...] }).
  function errores(r) {
    servicio(r);
    const lineas = r.errores && r.errores.length ? r.errores : [r.mensaje || "Ocurrió un error, intente de nuevo."];
    const caja = document.getElementById("mensajes");
    if (caja) caja.innerHTML = lineas.map((l) => "<div>" + esc(l) + "</div>").join("");
    else aviso(lineas.join("\n"), "error");
  }
  return { esc, dinero, hora, fechaHora, estilo, aviso, servicio, limpiar, errores };
})();

const Autenticacion = (() => {
  const INICIO = {
    Cliente: "htmlCliente/menu.html",
    Mesero: "htmlMesero/PrincipalMesero.html",
    Chef: "htmlChef/bienvenidoChef.html",
    Domiciliario: "htmlDomiciliario/bienvenidoDomiciliario.html",
    Administrador: "htmlAdmin/Principal.html",
  };

  function irAInicio(rol) {
    location.href = RAIZ + (INICIO[rol] || "login.html");
  }

  // Guardia de cada pantalla: exige sesión y rol; agrega "Cerrar sesión" al menú.
  function exigirRol(roles, extrasMenu) {
    const s = ClienteApi.sesionActual();
    if (!s || !s.token) { location.href = RAIZ + "login.html"; return null; }
    if (!roles.includes(s.rol)) { irAInicio(s.rol); return null; }
    const panel = document.querySelector(".menu-panel");
    if (panel) {
      (extrasMenu || []).forEach((e) => {
        const a = document.createElement("a");
        a.className = "menu-item";
        a.href = e.href;
        a.textContent = e.texto;
        panel.appendChild(a);
      });
      const salir = document.createElement("a");
      salir.className = "menu-item";
      salir.href = "#";
      salir.textContent = "Cerrar sesión";
      salir.addEventListener("click", async (ev) => {
        ev.preventDefault();
        await ClienteApi.cerrarSesion();
        location.href = RAIZ + "login.html";
      });
      panel.appendChild(salir);
    }
    return s;
  }

  function configurarLogin() {
    const s = ClienteApi.sesionActual();
    if (s && s.rol) { irAInicio(s.rol); return; }
    try {
      const m = sessionStorage.getItem("mensaje_login");
      if (m) {
        sessionStorage.removeItem("mensaje_login");
        Pantalla.errores({ errores: [m] });
      }
    } catch (e) { /* sin almacenamiento */ }
    document.getElementById("form-login").addEventListener("submit", async (e) => {
      e.preventDefault();
      Pantalla.limpiar();
      const r = await ClienteApi.iniciarSesion(
        document.getElementById("email").value.trim(),
        document.getElementById("contrasena").value
      );
      if (r.ok) irAInicio(r.datos.rol);
      else Pantalla.errores(r);
    });
  }

  function configurarRegistro() {
    document.getElementById("form-registro").addEventListener("submit", async (e) => {
      e.preventDefault();
      Pantalla.limpiar();
      const r = await ClienteApi.registrarCliente({
        nombre: document.getElementById("nombre").value.trim(),
        telefono: document.getElementById("telefono").value.trim(),
        email: document.getElementById("email").value.trim(),
        contrasena: document.getElementById("contrasena").value,
        acepta_tratamiento_datos: document.getElementById("acepta").checked,
      });
      if (r.ok) {
        Pantalla.aviso("Cuenta creada. Ya puede iniciar sesión.", "ok");
        setTimeout(() => { location.href = RAIZ + "login.html"; }, 1500);
      } else {
        Pantalla.errores(r);
      }
    });
  }

  return { irAInicio, exigirRol, configurarLogin, configurarRegistro };
})();

ClienteApi.alExpirarSesion(() => {
  try { sessionStorage.setItem("mensaje_login", "Su sesión expiró. Ingrese de nuevo."); } catch (e) { /* nada */ }
  location.href = RAIZ + "login.html";
});

if (document.getElementById("form-login")) Autenticacion.configurarLogin();
if (document.getElementById("form-registro")) Autenticacion.configurarRegistro();