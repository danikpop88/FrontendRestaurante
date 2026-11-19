// =====================================================================
// frontend/js/vistas_domiciliario.js
// Vistas del domiciliario: entregas asignadas, entregadas/devueltas y
// detalle con cierre de la entrega (RF-21, RF-23, RF-24).
// =====================================================================

(() => {
  const sesion = Autenticacion.exigirRol(["Domiciliario"]);
  if (!sesion) return;
  const esc = Pantalla.esc;

  function listar(entregados) {
    const marco = document.querySelector(".domiciliario-entregas, .domiciliario-entregados");
    marco.querySelectorAll(".bg-rectangle, .pedido-block, .floating-image").forEach((n) => n.remove());
    const zona = document.createElement("div");
    zona.style.cssText = "position:absolute;left:0;top:226px;width:100%;bottom:0;overflow-y:auto;padding:12px 0";
    marco.appendChild(zona);

    async function cargar() {
      const r = await ClienteApi.listarDomicilios();
      if (!Pantalla.servicio(r)) { zona.innerHTML = ""; return; }
      if (!r.ok) { Pantalla.errores(r); return; }
      const datos = r.datos.filter((d) => (entregados ? d.estado_entrega : !d.estado_entrega));
      zona.innerHTML = datos.length ? datos.map((d) => {
        const ent = d.estado_entrega === "Entregado";
        const href = !entregados ? "detallesPedido.html" : (ent ? "detallesPedidoEntregado.html" : "detallesPedidoDevuelto.html");
        return `<div style="background:#FCEFEF;padding:14px 20px;margin-bottom:12px;font-family:'Markazi Text',serif;font-size:25px">
          <div style="font-size:30px">Pedido #${d.id_pedido}:</div>
          <div>Nombre: ${esc(d.cliente.nombre)}</div>
          <div>Dirección: ${esc(d.direccion)}</div>
          ${entregados ? `<div>Estado: <b style="color:${ent ? "#14AE5C" : "#BF6A02"}">${esc(d.estado_entrega)}</b></div>` : ""}
          <a class="v-boton" href="${href}?id=${d.id_domicilio}">Detalles de pedido</a>
        </div>`;
      }).join("") : `<div class="v-vacio">${entregados ? "Todavía no hay entregas cerradas." : "No tiene entregas asignadas."}</div>`;
    }

    window.alRecibirAviso = cargar;
    cargar();
    setInterval(cargar, 10000);
  }

  async function detalle(accion) {
    const id = Number(new URLSearchParams(location.search).get("id"));
    const r = await ClienteApi.listarDomicilios();
    if (!Pantalla.servicio(r)) return;
    if (!r.ok) { Pantalla.errores(r); return; }
    const d = r.datos.find((x) => x.id_domicilio === id);
    if (!d) { Pantalla.aviso("No se encontró el domicilio.", "error"); return; }

    const filas = {
      ".label-nombre": "Nombre: " + d.cliente.nombre,
      ".label-telefono": "Teléfono: " + d.cliente.telefono,
      ".label-direccion": "Dirección: " + d.direccion,
      ".label-especificaciones": "Cobrar en efectivo: " + Pantalla.dinero(d.total),
      ".label-pedido": "Pedido: #" + d.id_pedido,
    };
    Object.keys(filas).forEach((sel) => {
      const el = document.querySelector(".info-card " + sel);
      el.textContent = filas[sel];
      el.style.fontSize = "22px";
      el.style.maxWidth = "370px";
      el.style.overflow = "hidden";
      el.style.textOverflow = "ellipsis";
    });

    if (!accion) return;
    document.querySelector(".btn-entregado a").addEventListener("click", async (e) => {
      e.preventDefault();
      const x = await ClienteApi.cerrarEntrega(id, "Entregado");
      if (x.ok) {
        Pantalla.aviso("Entrega registrada.", "ok");
        setTimeout(() => { location.href = "estadoPedido.html"; }, 1000);
      } else {
        Pantalla.errores(x);
      }
    });
    document.querySelector(".btn-devuelto a").addEventListener("click", async (e) => {
      e.preventDefault();
      const motivo = prompt("Motivo de la devolución:");
      if (motivo === null) return;
      const x = await ClienteApi.cerrarEntrega(id, "Devuelto", motivo.trim());
      if (x.ok) {
        Pantalla.aviso("Devolución registrada.", "ok");
        setTimeout(() => { location.href = "estadoPedido.html"; }, 1000);
      } else {
        Pantalla.errores(x);
      }
    });
  }

  const pagina = location.pathname.split("/").pop();
  if (pagina === "entregasDomiciliario.html") listar(false);
  else if (pagina === "estadoPedido.html") listar(true);
  else if (pagina === "detallesPedido.html") detalle(true);
  else if (pagina === "detallesPedidoEntregado.html" || pagina === "detallesPedidoDevuelto.html") detalle(false);
})();