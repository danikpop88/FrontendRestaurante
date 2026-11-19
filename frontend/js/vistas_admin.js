// =====================================================================
// frontend/js/vistas_admin.js
// Vistas del administrador: menú (listar, crear, editar, agotado),
// ventas y reservas, y cuentas del personal (RF-10 a RF-14, RF-01).
// =====================================================================

(() => {
  const sesion = Autenticacion.exigirRol(["Administrador"], [{ texto: "Cuentas del personal", href: "cuentas.html" }]);
  if (!sesion) return;
  const esc = Pantalla.esc;
  const dinero = Pantalla.dinero;
  const p2 = (n) => String(n).padStart(2, "0");
  const fechaISO = (d) => `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())}`;

  function numero(t) {
    t = String(t).trim();
    if (!t) return null;
    if (/^\d{1,3}(\.\d{3})+$/.test(t)) t = t.replace(/\./g, "");
    else t = t.replace(",", ".");
    const n = Number(t);
    return isNaN(n) ? null : n;
  }

  function opcionesCategoria(productos, actual) {
    const cats = Array.from(new Set(productos.map((p) => p.categoria)));
    if (actual && !cats.includes(actual)) cats.push(actual);
    return cats.map((c) => `<option value="${esc(c)}" ${c === actual ? "selected" : ""}>${esc(c)}</option>`).join("");
  }

  // Botones Disponible / Agotado: devuelve una función que da el valor actual.
  function selectorDisponibilidad(btnSi, btnNo, inicial) {
    let disponible = inicial;
    function marcar() {
      btnSi.classList.toggle("sel", disponible);
      btnNo.classList.toggle("sel", !disponible);
    }
    btnSi.addEventListener("click", (e) => { e.preventDefault(); disponible = true; marcar(); });
    btnNo.addEventListener("click", (e) => { e.preventDefault(); disponible = false; marcar(); });
    marcar();
    return () => disponible;
  }

  // ---------- Gestión del menú ----------
  function principal() {
    const pantalla = document.querySelector(".pantalla");
    pantalla.querySelectorAll(".producto, .estado").forEach((n) => { n.style.display = "none"; });
    pantalla.querySelectorAll('a[href$="actualizarPlato.html"], a[href$="eliminarPlato.html"]').forEach((n) => { n.style.display = "none"; });
    document.querySelector(".hero").insertAdjacentHTML("beforeend",
      '<div class="pill" style="left:26px;top:320px"><div class="pill-texto"><a href="../htmlAdmin/cuentas.html">Cuentas del personal</a></div></div>');
    const zona = document.createElement("div");
    zona.style.cssText = "position:absolute;left:18px;top:627px;width:420px";
    pantalla.appendChild(zona);

    async function cargar() {
      const r = await ClienteApi.listarMenu();
      if (!Pantalla.servicio(r)) { zona.innerHTML = ""; return; }
      if (!r.ok) { Pantalla.errores(r); return; }
      zona.innerHTML = r.datos.length ? r.datos.map((p) => `<div class="v-tarjeta">
          <div style="display:flex;justify-content:space-between;gap:8px">
            <div style="flex:1"><b>${esc(p.nombre)}</b> <small>(${esc(p.categoria)})</small><br>
              <span style="color:#495E57">${esc(p.descripcion || "")}</span><br><b>${dinero(p.precio)}</b></div>
            <div style="text-align:right">
              <button type="button" class="v-boton" style="background:${p.disponible ? "#2DB98B" : "#495E57"};color:#fff" data-id="${p.id_producto}" data-disp="${p.disponible}">${p.disponible ? "Disponible" : "Agotado"}</button><br>
              <a class="v-boton gris" href="actualizarPlato.html?id=${p.id_producto}">✏️ Editar</a>
            </div>
          </div></div>`).join("") : '<div class="v-vacio">Todavía no hay productos.</div>';
      pantalla.style.height = (627 + zona.offsetHeight + 40) + "px";
    }

    zona.addEventListener("click", async (e) => {
      const b = e.target.closest("button[data-id]");
      if (!b) return;
      const r = await ClienteApi.cambiarDisponibilidad(Number(b.dataset.id), b.dataset.disp !== "true");
      if (r.ok) cargar(); else Pantalla.errores(r);
    });
    cargar();
  }

  // ---------- Crear producto (RF-13) ----------
  async function crear() {
    const cont = document.querySelector(".product-card-container");
    const rm = await ClienteApi.listarMenu();
    Pantalla.servicio(rm);
    cont.insertAdjacentHTML("beforeend",
      `<label class="form-label" style="left:17px;top:660px">Categoría:</label>
       <select id="categoria" class="input-field" style="left:8px;top:690px;width:344px;height:40px">${opcionesCategoria(rm.ok ? rm.datos : [], "")}</select>`);
    const esDisponible = selectorDisponibilidad(document.querySelector(".btn-available"), document.querySelector(".btn-out-of-stock"), true);

    async function enviar() {
      const precio = document.getElementById("product-price").value;
      const cuerpo = {
        nombre: document.getElementById("product-name").value.trim(),
        categoria: document.getElementById("categoria").value,
        precio: precio === "" ? null : Number(precio),
      };
      const desc = document.getElementById("product-description").value.trim();
      if (desc) cuerpo.descripcion = desc;
      const r = await ClienteApi.crearProducto(cuerpo);
      if (!r.ok) { Pantalla.errores(r); return; }
      if (!esDisponible()) await ClienteApi.cambiarDisponibilidad(r.datos.id_producto, false);
      Pantalla.aviso("Producto creado.", "ok");
      setTimeout(() => { location.href = "Principal.html"; }, 1000);
    }
    document.querySelector(".btn-submit").addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); enviar(); }, true);
    document.querySelector(".product-form").addEventListener("submit", (e) => e.preventDefault());
  }

  // ---------- Editar producto (RF-12, RF-14) ----------
  async function editar() {
    const id = Number(new URLSearchParams(location.search).get("id"));
    const r = await ClienteApi.listarMenu();
    if (!Pantalla.servicio(r)) return;
    if (!r.ok) { Pantalla.errores(r); return; }
    const p = r.datos.find((x) => x.id_producto === id);
    if (!p) { Pantalla.aviso("Producto no encontrado.", "error"); return; }

    document.getElementById("nombre").value = p.nombre;
    document.getElementById("descripcion").value = p.descripcion || "";
    document.getElementById("precio").value = String(Number(p.precio));
    document.querySelector(".pantalla").insertAdjacentHTML("beforeend",
      `<div class="etiqueta" style="top:672px">Categoría:</div>
       <select id="categoria" class="campo" style="left:8px;top:698px">${opcionesCategoria(r.datos, p.categoria)}</select>`);
    const esDisponible = selectorDisponibilidad(document.querySelector(".boton-disponible"), document.querySelector(".boton-agotado"), p.disponible);

    async function enviar() {
      const x = await ClienteApi.editarProducto(id, {
        nombre: document.getElementById("nombre").value.trim(),
        categoria: document.getElementById("categoria").value,
        precio: numero(document.getElementById("precio").value),
        descripcion: document.getElementById("descripcion").value.trim(),
      });
      if (!x.ok) { Pantalla.errores(x); return; }
      if (esDisponible() !== p.disponible) {
        const y = await ClienteApi.cambiarDisponibilidad(id, esDisponible());
        if (!y.ok) { Pantalla.errores(y); return; }
      }
      Pantalla.aviso("Producto actualizado.", "ok");
      setTimeout(() => { location.href = "Principal.html"; }, 1000);
    }
    document.querySelector("form").addEventListener("submit", (e) => { e.preventDefault(); enviar(); });
  }

  // ---------- Ventas y reservas (RF-10, RF-11) ----------
  function semanaISO(d) {
    const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    const dia = t.getUTCDay() || 7;
    t.setUTCDate(t.getUTCDate() + 4 - dia);
    const ini = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
    return `${t.getUTCFullYear()}-W${p2(Math.ceil(((t - ini) / 86400000 + 1) / 7))}`;
  }
  function lunesDeSemana(valor) {
    const [a, s] = valor.split("-W").map(Number);
    const cuatro = new Date(Date.UTC(a, 0, 4));
    const dia = cuatro.getUTCDay() || 7;
    const l = new Date(cuatro);
    l.setUTCDate(cuatro.getUTCDate() - dia + 1 + (s - 1) * 7);
    return new Date(l.getUTCFullYear(), l.getUTCMonth(), l.getUTCDate());
  }

  function ventas() {
    Pantalla.estilo(".contenido-vista{display:none!important}");
    const pantalla = document.querySelector(".pantalla");
    const selector = document.createElement("div");
    selector.className = "selector-fecha";
    selector.innerHTML = '<input class="selector-fecha-input" id="v-periodo" style="border:none;outline:none;width:100%;font:16px Inter,sans-serif;background:transparent">';
    pantalla.appendChild(selector);
    const informe = document.createElement("div");
    informe.style.cssText = "position:absolute;left:18px;top:262px;width:420px";
    pantalla.appendChild(informe);
    const input = document.getElementById("v-periodo");
    let periodo = "diario";

    function marcar() {
      ["diario", "semanal", "mensual"].forEach((p) => document.querySelector(".filtro-" + p).classList.toggle("filtro-activo", p === periodo));
    }
    function ajustar() {
      const hoy = new Date();
      input.type = { diario: "date", semanal: "week", mensual: "month" }[periodo];
      input.value = periodo === "diario" ? fechaISO(hoy) : (periodo === "semanal" ? semanaISO(hoy) : `${hoy.getFullYear()}-${p2(hoy.getMonth() + 1)}`);
    }
    function rango() {
      const v = input.value;
      if (!v) return null;
      if (periodo === "diario") return [v, v];
      if (periodo === "semanal") {
        const l = lunesDeSemana(v);
        const f = new Date(l);
        f.setDate(l.getDate() + 6);
        return [fechaISO(l), fechaISO(f)];
      }
      const [a, m] = v.split("-").map(Number);
      return [`${a}-${p2(m)}-01`, fechaISO(new Date(a, m, 0))];
    }

    async function cargar() {
      const rg = rango();
      if (!rg) { Pantalla.aviso("Seleccione una fecha.", "error"); return; }
      const [rv, rr] = await Promise.all([ClienteApi.consultarVentas(rg[0], rg[1]), ClienteApi.listarReservas()]);
      if (!Pantalla.servicio(rv)) { informe.innerHTML = ""; return; }
      if (!rv.ok) { Pantalla.errores(rv); return; }
      const v = rv.datos;
      const filas = v.datos.map((x) => `<tr><td>#${x.id_pedido}</td><td>${Pantalla.fechaHora(x.fecha)}</td><td>${dinero(x.total)}</td><td>${esc(x.estado_pago)}</td></tr>`).join("");
      const reservas = rr.ok
        ? (rr.datos.length ? rr.datos.map((x) => `<div class="v-tarjeta"><b>${esc(x.nombre_titular)}</b> · Mesa ${esc(x.numero_mesa)}<br>${esc(x.fecha_reserva)} · ${esc(String(x.hora_reserva).slice(0, 5))} · ${esc(x.telefono_titular)}</div>`).join("")
          : '<div class="v-vacio">No hay reservas vigentes.</div>')
        : '<div class="v-vacio">No se pudieron cargar las reservas.</div>';
      informe.innerHTML = `
        <div style="display:flex;gap:12px;margin-bottom:12px">
          <div class="v-tarjeta" style="flex:1;margin:0"><b>Ventas totales</b><br><span style="font:700 28px Karla,sans-serif">${dinero(v.total_ventas)}</span></div>
          <div class="v-tarjeta" style="flex:1;margin:0"><b>Pedidos vendidos</b><br><span style="font:700 28px Karla,sans-serif">${v.cantidad}</span></div>
        </div>
        ${v.datos.length ? `<table class="v-tabla"><tr><th>Pedido</th><th>Fecha</th><th>Total</th><th>Pago</th></tr>${filas}</table>` : '<div class="v-vacio">No hay ventas en este periodo.</div>'}
        <h3 style="font:700 20px Karla,sans-serif;margin:20px 0 10px">Reservas vigentes</h3>${reservas}`;
      pantalla.style.height = (262 + informe.offsetHeight + 40) + "px";
    }

    ["diario", "semanal", "mensual"].forEach((p) => {
      document.querySelector(".filtro-" + p).addEventListener("click", () => { periodo = p; marcar(); ajustar(); cargar(); });
    });
    document.querySelector(".boton-informe").addEventListener("click", cargar);
    input.addEventListener("change", cargar);
    marcar();
    ajustar();
    cargar();
  }

  // ---------- Cuentas del personal (RF-01) ----------
  function cuentas() {
    const f = document.getElementById("form-cuenta");
    f.addEventListener("submit", async (e) => {
      e.preventDefault();
      Pantalla.limpiar();
      const g = (id) => document.getElementById(id).value.trim();
      const r = await ClienteApi.crearEmpleado({
        nombre: g("nombre"), telefono: g("telefono"), email: g("email"),
        contrasena: document.getElementById("contrasena").value, tipo_cargo: g("tipo_cargo"),
      });
      if (r.ok) { Pantalla.aviso("Cuenta creada.", "ok"); f.reset(); }
      else Pantalla.errores(r);
    });
  }

  const pagina = location.pathname.split("/").pop();
  const mapa = { "Principal.html": principal, "ventasReservas.html": ventas, "crearPlato.html": crear, "actualizarPlato.html": editar, "cuentas.html": cuentas };
  if (mapa[pagina]) mapa[pagina]();
})();