// =====================================================================
// frontend/js/vistas_chef.js
// Vistas del chef: cola de cocina (tomar / marcar listo) y las órdenes
// marcadas listas en esta sesión (RF-18, RF-19, RF-20).
// =====================================================================

(() => {
  const sesion = Autenticacion.exigirRol(["Chef"]);
  if (!sesion) return;
  const esc = Pantalla.esc;
  const CLAVE = "listas_chef";
  const leerListas = () => { try { return JSON.parse(sessionStorage.getItem(CLAVE) || "[]"); } catch (e) { return []; } };
  const guardarListas = (l) => { try { sessionStorage.setItem(CLAVE, JSON.stringify(l)); } catch (e) { /* nada */ } };

  function pendientes() {
    const marco = document.querySelector(".chef-ordenes");
    marco.querySelectorAll(".order-card").forEach((n) => { n.style.display = "none"; });
    const zona = document.createElement("div");
    zona.style.cssText = "position:absolute;left:16px;top:150px;width:398px;height:665px;overflow-y:auto";
    zona.innerHTML = `<div>
        <button type="button" class="v-boton gris" data-tipo="">Todos</button>
        <button type="button" class="v-boton gris" data-tipo="EN_RESTAURANTE">Restaurante</button>
        <button type="button" class="v-boton gris" data-tipo="DOMICILIO">Domicilio</button>
      </div><div id="lista"></div>`;
    marco.appendChild(zona);
    const lista = zona.querySelector("#lista");
    let tipo = "";

    function tarjeta(p) {
      const dom = p.tipo_pedido === "DOMICILIO";
      const notas = p.detalle.filter((d) => d.observaciones_especiales).map((d) => d.observaciones_especiales);
      return `<div class="v-tarjeta">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <b style="font-size:22px">${dom ? "Domicilio #" + p.id_pedido : "Mesa #" + esc(p.numero_mesa)}</b>
          <span style="color:#777">${Pantalla.hora(p.fecha)}</span>
        </div>
        <div style="background:${dom ? "#F9C22E" : "#CFF7D3"};display:inline-block;border-radius:8px;padding:4px 10px;margin:6px 0">${dom ? "Domicilio (para enviar)" : "Restaurante"}</div>
        <div>Pedido:<br>${p.detalle.map((d) => `${d.cantidad}x &nbsp; ${esc(d.nombre)}`).join("<br>")}</div>
        ${notas.length ? `<div>Nota: ${esc(notas.join("; "))}</div>` : ""}
        ${p.estado_pedido === "Recibido"
          ? `<button type="button" class="v-boton" data-tomar="${p.id_pedido}">Tomar pedido</button>`
          : `<button type="button" class="v-boton" data-listo="${p.id_pedido}" data-tipo="${p.tipo_pedido}" data-mesa="${esc(p.numero_mesa)}">Pedido listo</button>`}
      </div>`;
    }

    async function cargar() {
      const r = await ClienteApi.colaCocina(tipo);
      if (!Pantalla.servicio(r)) { lista.innerHTML = ""; return; }
      if (!r.ok) { Pantalla.errores(r); return; }
      lista.innerHTML = r.datos.length ? r.datos.map(tarjeta).join("") : '<div class="v-vacio">No hay órdenes pendientes.</div>';
    }

    zona.addEventListener("click", async (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.tipo !== undefined && !b.dataset.listo) { tipo = b.dataset.tipo; cargar(); return; }
      if (b.dataset.tomar) {
        const r = await ClienteApi.tomarPedido(Number(b.dataset.tomar));
        if (r.ok) cargar(); else Pantalla.errores(r);
      } else if (b.dataset.listo) {
        const r = await ClienteApi.marcarListo(Number(b.dataset.listo));
        if (r.ok) {
          const l = leerListas();
          l.push({ texto: b.dataset.tipo === "DOMICILIO"
            ? `El pedido a domicilio #${b.dataset.listo} está listo para entrega.`
            : `La orden de la Mesa #${b.dataset.mesa} ha sido enviada al mesero.` });
          guardarListas(l);
          Pantalla.aviso("Aviso enviado.", "ok");
          cargar();
        } else {
          Pantalla.errores(r);
        }
      }
    });

    cargar();
    setInterval(cargar, 8000);
  }

  function listas() {
    const marco = document.querySelector(".chef-notificaciones");
    marco.querySelectorAll(".notification-card").forEach((n) => { n.style.display = "none"; });
    const zona = document.createElement("div");
    zona.style.cssText = "position:absolute;left:33px;top:100px;width:363px;height:460px;overflow-y:auto";
    marco.appendChild(zona);

    function pintar() {
      const l = leerListas();
      zona.innerHTML = l.length ? l.map((x, i) => `<div class="v-tarjeta" style="text-align:center">
          <b>¡Pedido listo!</b><br>${esc(x.texto)}<br>
          <button type="button" class="v-boton gris" data-i="${i}">Aceptar</button></div>`).join("")
        : '<div class="v-vacio">No hay órdenes listas por confirmar.</div>';
    }
    zona.addEventListener("click", (e) => {
      const b = e.target.closest("[data-i]");
      if (!b) return;
      const l = leerListas();
      l.splice(Number(b.dataset.i), 1);
      guardarListas(l);
      pintar();
    });
    pintar();
  }

  const pagina = location.pathname.split("/").pop();
  if (pagina === "ordenesPendientesChef.html") pendientes();
  else if (pagina === "ordenesListasChef.html") listas();
})();