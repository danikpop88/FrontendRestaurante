// =====================================================================
// frontend/js/vistas_mesero.js
// Vistas del mesero: nueva comanda / modificar (?editar=ID) y lista de
// órdenes con avisos de plato listo (RF-16, RF-17).
// =====================================================================

(() => {
  const sesion = Autenticacion.exigirRol(["Mesero"]);
  if (!sesion) return;
  const esc = Pantalla.esc;

  async function comanda() {
    const idEditar = new URLSearchParams(location.search).get("editar");
    const tarjeta = document.querySelector(".form-card");
    const boton = document.querySelector(".btn-comanda");
    boton.textContent = idEditar ? "Guardar cambios" : "Nueva comanda a cocina";

    const rm = await ClienteApi.listarMenu();
    if (!Pantalla.servicio(rm)) { tarjeta.innerHTML = '<div class="v-vacio">El servicio no está disponible.</div>'; return; }
    if (!rm.ok) { Pantalla.errores(rm); return; }

    const opciones = '<option value="">Seleccione un producto</option>' + rm.datos.map((p) =>
      `<option value="${p.id_producto}" ${p.disponible ? "" : "disabled"}>${esc(p.nombre)}${p.disponible ? "" : " (Agotado)"}</option>`).join("");

    tarjeta.innerHTML = `
      <div class="form-field"><label for="mesero">Mesero</label><input type="text" id="mesero" readonly value="${esc(sesion.usuario.nombre)}"></div>
      <div class="form-field"><label for="mesa"># de mesa</label><input type="number" min="1" id="mesa" placeholder="Ejemplo: 1, 2, ..."></div>
      <div class="form-field"><label>Comanda de productos</label><div id="filas" style="width:100%"></div></div>
      <div class="form-field no-label"><button type="button" class="v-boton gris" id="mas">+ Agregar otro producto o bebida</button></div>
      <div class="form-field"><label for="notas">Notas adicionales</label><input type="text" id="notas" placeholder="Ejemplo: Sin hielo, sin cebolla, ..."></div>
      <div id="mensajes" class="v-mensajes"></div>`;

    const filas = document.getElementById("filas");
    function agregarFila(id, cant) {
      const f = document.createElement("div");
      f.className = "fila";
      f.style.cssText = "display:flex;gap:6px;margin-bottom:8px;align-items:center";
      f.innerHTML = `<select class="v-select" style="flex:1">${opciones}</select>
        <input class="cant" type="number" min="1" value="${cant || 1}" style="width:70px;min-width:0;padding:10px 6px">
        <button type="button" class="v-boton rojo" style="margin:0">✕</button>`;
      if (id) f.querySelector("select").value = String(id);
      f.querySelector("button").onclick = () => f.remove();
      filas.appendChild(f);
    }
    document.getElementById("mas").onclick = () => agregarFila();

    if (idEditar) {
      const rp = await ClienteApi.obtenerPedido(idEditar);
      if (rp.ok) {
        document.getElementById("mesa").value = rp.datos.numero_mesa || "";
        rp.datos.detalle.forEach((d) => agregarFila(d.id_producto, d.cantidad));
        const nota = rp.datos.detalle.find((d) => d.observaciones_especiales);
        if (nota) document.getElementById("notas").value = nota.observaciones_especiales;
      } else {
        Pantalla.errores(rp);
      }
    }
    if (!filas.children.length) agregarFila();

    boton.onclick = async () => {
      Pantalla.limpiar();
      const mapa = {};
      filas.querySelectorAll(".fila").forEach((f) => {
        const id = Number(f.querySelector("select").value);
        const cant = Number(f.querySelector(".cant").value);
        if (id) mapa[id] = (mapa[id] || 0) + cant;
      });
      const nota = document.getElementById("notas").value.trim();
      const items = Object.keys(mapa).map((id) => {
        const it = { id_producto: Number(id), cantidad: mapa[id] };
        if (nota) it.observaciones_especiales = nota;
        return it;
      });
      if (!items.length) { Pantalla.errores({ errores: ["Agregue al menos un producto."] }); return; }
      const mesa = Number(document.getElementById("mesa").value);
      const cuerpo = { items: items };
      if (mesa > 0) cuerpo.numero_mesa = mesa;

      let r;
      if (idEditar) r = await ClienteApi.modificarPedido(idEditar, cuerpo);
      else { cuerpo.tipo_pedido = "EN_RESTAURANTE"; r = await ClienteApi.crearPedido(cuerpo); }

      if (!r.ok) { Pantalla.errores(r); return; }
      Pantalla.aviso(idEditar ? "Orden modificada." : "Comanda enviada a cocina.", "ok");
      setTimeout(() => { location.href = idEditar ? "ordenesListas.html" : "PrincipalMesero.html"; }, 1000);
    };
  }

  function ordenes() {
    const tarjeta = document.querySelector(".orders-card");
    tarjeta.querySelectorAll(".order-item").forEach((n) => n.remove());
    tarjeta.style.overflowY = "auto";
    tarjeta.style.paddingTop = "96px";
    const lista = document.createElement("div");
    tarjeta.appendChild(lista);
    const ESTADOS = { Recibido: "Recibida", EnCocina: "En cocina", EnCamino: "Lista para llevar a la mesa", Entregado: "Entregada" };

    async function cargar() {
      const r = await ClienteApi.listarPedidos();
      if (!Pantalla.servicio(r)) { lista.innerHTML = ""; return; }
      if (!r.ok) { Pantalla.errores(r); return; }
      if (!r.datos.length) { lista.innerHTML = '<div class="v-vacio">No hay órdenes todavía.</div>'; return; }
      lista.innerHTML = r.datos.slice().sort((a, b) => b.id_pedido - a.id_pedido).map((p) => `
        <div class="v-tarjeta" style="background:${p.estado_pedido === "EnCamino" ? "#CFF7D3" : "#D9D9D9"}">
          <b>Mesa: ${esc(p.numero_mesa)}</b> · ${ESTADOS[p.estado_pedido] || esc(p.estado_pedido)}<br>
          Comanda:<br>${p.detalle.map((d) => `${esc(d.nombre)} (${d.cantidad}x)`).join("<br>")}
          ${p.estado_pedido === "Recibido" ? `<div>
            <a class="v-boton" href="PrincipalMesero.html?editar=${p.id_pedido}">Modificar</a>
            <button type="button" class="v-boton rojo" data-cancelar="${p.id_pedido}">Cancelar</button></div>` : ""}
        </div>`).join("");
    }

    lista.addEventListener("click", async (e) => {
      const b = e.target.closest("[data-cancelar]");
      if (!b) return;
      const r = await ClienteApi.cancelarPedido(Number(b.dataset.cancelar));
      if (r.ok) { Pantalla.aviso("Orden cancelada.", "ok"); cargar(); }
      else Pantalla.errores(r);
    });

    window.alRecibirAviso = cargar;
    cargar();
    setInterval(cargar, 10000);
  }

  const pagina = location.pathname.split("/").pop();
  if (pagina === "PrincipalMesero.html") comanda();
  else if (pagina === "ordenesListas.html") ordenes();
})();