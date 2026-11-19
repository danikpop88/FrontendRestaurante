// =====================================================================
// frontend/js/vistas_cliente.js
// Vistas del cliente: menú, carrito/confirmar pedido y seguimiento.
// El carrito vive aquí hasta confirmar; el backend recalcula el total.
// =====================================================================

(() => {
  const sesion = Autenticacion.exigirRol(["Cliente"]);
  if (!sesion) return;
  const esc = Pantalla.esc;
  const dinero = Pantalla.dinero;

  const CATEGORIAS = { "Todas": "", "Entradas": "Entradas", "Platos fuertes": "Platos Fuertes", "Postres": "Postres", "Bebidas": "Bebidas" };

  const Carrito = {
    leer() { try { return JSON.parse(sessionStorage.getItem("carrito") || "[]"); } catch (e) { return []; } },
    guardar(l) { try { sessionStorage.setItem("carrito", JSON.stringify(l)); } catch (e) { /* nada */ } },
    agregar(p) {
      const l = this.leer();
      const x = l.find((i) => i.id_producto === p.id_producto);
      if (x) x.cantidad++;
      else l.push({ id_producto: p.id_producto, nombre: p.nombre, precio: p.precio, cantidad: 1 });
      this.guardar(l);
    },
    vaciar() { this.guardar([]); },
  };

  // ---------- Menú (RF-02, RF-03) ----------
  function menu() {
    const columna = document.querySelector(".lista-columna");
    const pagina = document.querySelector(".pagina");
    const vermas = document.querySelector(".boton-vermas");
    if (vermas) vermas.style.display = "none";
    columna.innerHTML = '<div class="v-vacio">Cargando menú...</div>';
    let categoria = "";
    let productos = {};

    async function cargar() {
      const r = await ClienteApi.listarMenu(categoria);
      if (!Pantalla.servicio(r)) { columna.innerHTML = ""; return; }
      if (!r.ok) { Pantalla.errores(r); return; }
      if (!r.datos.length) {
        columna.innerHTML = '<div class="v-vacio">Todavía no hay productos en esta categoría.</div>';
        return;
      }
      productos = {};
      columna.innerHTML = r.datos.map((p) => {
        productos[p.id_producto] = p;
        return `<div class="plato">
          <div class="plato-fila">
            <div class="plato-texto">
              <div class="plato-nombre">${esc(p.nombre)}</div>
              <div class="plato-descripcion">${esc(p.descripcion || "")}</div>
              <div class="plato-precio">${dinero(p.precio)}</div>
            </div>
            ${p.imagen ? `<img class="plato-imagen" src="${esc(p.imagen)}" alt="">` : '<div class="plato-imagen"></div>'}
          </div>
          <div class="boton-seleccionar boton-seleccionar--arroz" data-id="${p.id_producto}" ${p.disponible ? "" : 'data-agotado="1" style="opacity:.5;cursor:not-allowed"'}>
            <div class="boton-texto">${p.disponible ? "Seleccionar" : "Agotado"}</div>
          </div>
          <div class="plato-linea"></div>
        </div>`;
      }).join("");
      pagina.style.height = (578 + 16 + r.datos.length * 139 + 80) + "px";
    }

    columna.addEventListener("click", (e) => {
      const b = e.target.closest(".boton-seleccionar");
      if (!b || b.dataset.agotado) return;
      Carrito.agregar(productos[b.dataset.id]);
      Pantalla.aviso("Agregado al carrito.", "ok");
    });

    document.querySelectorAll(".categoria").forEach((b) => {
      b.addEventListener("click", () => {
        document.querySelectorAll(".categoria").forEach((x) => { x.style.background = "#EDEFEE"; });
        b.style.background = "#F4CE14";
        categoria = CATEGORIAS[b.textContent.trim()] || "";
        cargar();
      });
    });
    cargar();
  }

  // ---------- Carrito, dirección y confirmar (RF-03, 04, 06, 07) ----------
  function pedido() {
    document.querySelector(".campo--telefono").style.display = "none";
    document.querySelector(".campo--email").style.display = "none";
    const campoNombre = document.getElementById("nombres");
    const campoDir = document.getElementById("direccion");
    campoNombre.value = sesion.usuario.nombre || "";
    campoNombre.readOnly = true;
    campoDir.value = sesion.usuario.direccion || "";

    const zona = document.querySelector(".tabla-items");
    const total = document.querySelector(".tabla-total");
    zona.style.height = "200px";
    zona.style.overflowY = "auto";
    zona.style.whiteSpace = "normal";

    async function pintar() {
      const lista = Carrito.leer();
      if (!lista.length) {
        zona.innerHTML = '<div>Su carrito está vacío. <a href="menu.html" style="text-decoration:underline">Ir al menú</a></div>';
        total.textContent = "TOTAL: $0";
        return;
      }
      zona.innerHTML = lista.map((i) => `<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px">
        <button type="button" class="v-boton gris" style="padding:2px 8px;margin:0" data-menos="${i.id_producto}">−</button>
        <b>${i.cantidad}x</b>
        <button type="button" class="v-boton gris" style="padding:2px 8px;margin:0" data-mas="${i.id_producto}">+</button>
        <span style="flex:1">${esc(i.nombre)}</span>
        <span>${dinero(i.precio * i.cantidad)}</span>
        <button type="button" class="v-boton rojo" style="padding:2px 8px;margin:0" data-quitar="${i.id_producto}">✕</button>
      </div>`).join("");
      const r = await ClienteApi.resumenPedido({
        tipo_pedido: "DOMICILIO",
        direccion: campoDir.value.trim() || sesion.usuario.direccion || "Por definir",
        metodo_pago: "CONTRA_ENTREGA",
        items: lista.map((i) => ({ id_producto: i.id_producto, cantidad: i.cantidad })),
      });
      if (!Pantalla.servicio(r)) { total.textContent = "TOTAL: —"; return; }
      if (r.ok) total.textContent = "TOTAL (incluye IVA 19 %):  " + dinero(r.datos.total);
      else { total.textContent = "TOTAL: —"; Pantalla.errores(r); }
    }

    zona.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      let l = Carrito.leer();
      const id = Number(b.dataset.mas || b.dataset.menos || b.dataset.quitar);
      const item = l.find((i) => i.id_producto === id);
      if (!item) return;
      if (b.dataset.mas) item.cantidad++;
      else if (b.dataset.menos) { if (item.cantidad > 1) item.cantidad--; }
      else l = l.filter((i) => i.id_producto !== id);
      Carrito.guardar(l);
      pintar();
    });

    document.querySelector(".boton-texto--confirmar a").addEventListener("click", async (e) => {
      e.preventDefault();
      const lista = Carrito.leer();
      const dir = campoDir.value.trim();
      if (!lista.length) { Pantalla.aviso("Agregue productos al carrito antes de confirmar.", "error"); return; }
      if (!dir) { Pantalla.aviso("Escriba la dirección de entrega.", "error"); return; }
      let r = await ClienteApi.guardarDireccion(dir);
      if (!r.ok) { Pantalla.errores(r); return; }
      r = await ClienteApi.crearPedido({
        tipo_pedido: "DOMICILIO",
        direccion: dir,
        metodo_pago: "CONTRA_ENTREGA",
        items: lista.map((i) => ({ id_producto: i.id_producto, cantidad: i.cantidad })),
      });
      if (!r.ok) { Pantalla.errores(r); return; }
      Carrito.vaciar();
      try { sessionStorage.setItem("ultimo_pedido", r.datos.id_pedido); } catch (err) { /* nada */ }
      location.href = "seguimiento.html";
    });

    pintar();
  }

  // ---------- Seguimiento y cancelar (RF-05) ----------
  function seguimiento() {
    const cont = document.querySelector(".order-steps-container");
    const PASOS = ["Pedido realizado", "En cocina", "En camino", "Pedido entregado"];
    const ORDEN = ["Recibido", "EnCocina", "EnCamino", "Entregado"];
    const MENSAJES = [
      "Recibimos su pedido. Puede cancelarlo durante los primeros 5 minutos.",
      "Estamos preparando su pedido.",
      "Tu pedido va en dirección a tu ubicación",
      "¡Buen provecho!",
    ];

    async function cargar() {
      const r = await ClienteApi.listarPedidos();
      if (!Pantalla.servicio(r)) { cont.innerHTML = ""; return; }
      if (!r.ok) { Pantalla.errores(r); return; }
      if (!r.datos.length) { cont.innerHTML = '<div class="v-vacio">Todavía no tiene pedidos.</div>'; return; }
      let id = 0;
      try { id = Number(sessionStorage.getItem("ultimo_pedido")); } catch (e) { /* nada */ }
      const p = r.datos.find((x) => x.id_pedido === id) || r.datos.reduce((a, b) => (b.id_pedido > a.id_pedido ? b : a));
      const n = ORDEN.indexOf(p.estado_pedido);
      cont.innerHTML =
        `<p class="status-message"><b>Pedido #${p.id_pedido}</b> · Total ${dinero(p.total)}</p>` +
        PASOS.map((t, i) => `<div class="step-card"><span>${t}</span>${i <= n ? '<div class="check-icon"></div>' : ""}</div>`).join("") +
        `<p class="status-message">${MENSAJES[n] || ""}</p>` +
        (n === 0 ? `<button type="button" class="v-boton rojo" data-cancelar="${p.id_pedido}">Cancelar pedido</button>` : "");
    }

    cont.addEventListener("click", async (e) => {
      const b = e.target.closest("[data-cancelar]");
      if (!b) return;
      const r = await ClienteApi.cancelarPedido(Number(b.dataset.cancelar));
      if (r.ok) {
        Pantalla.aviso("Pedido cancelado.", "ok");
        try { sessionStorage.removeItem("ultimo_pedido"); } catch (err) { /* nada */ }
        setTimeout(() => { location.href = "menu.html"; }, 1200);
      } else {
        Pantalla.errores(r);
      }
    });

    cargar();
    setInterval(cargar, 10000);
  }

  const pagina = location.pathname.split("/").pop();
  if (pagina === "menu.html") menu();
  else if (pagina === "pedido.html") pedido();
  else if (pagina === "seguimiento.html") seguimiento();
})();