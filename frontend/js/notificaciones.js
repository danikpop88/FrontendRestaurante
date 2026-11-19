// =====================================================================
// frontend/js/notificaciones.js
// Recepción de avisos simulados: pide los avisos sin leer cada 5 s,
// los muestra en pantalla y los marca como leídos (Mesero y Domiciliario).
// =====================================================================

(() => {
  const s = ClienteApi.sesionActual();
  if (!s || !["Mesero", "Domiciliario"].includes(s.rol)) return;

  const vistos = new Set();
  const caja = document.createElement("div");
  caja.className = "v-avisos";
  document.body.appendChild(caja);

  async function sondear() {
    const r = await ClienteApi.listarAvisos(false);
    if (!r.ok) return; // sin servicio o error: no hay nada que mostrar
    for (const a of r.datos) {
      if (vistos.has(a.id_aviso)) continue;
      vistos.add(a.id_aviso);
      const t = document.createElement("div");
      t.className = "v-pedido-listo";
      t.textContent = a.mensaje;
      t.onclick = () => t.remove();
      caja.appendChild(t);
      setTimeout(() => t.remove(), 15000);
      await ClienteApi.marcarAvisoLeido(a.id_aviso);
    }
    if (r.datos.length && typeof window.alRecibirAviso === "function") window.alRecibirAviso();
  }

  sondear();
  setInterval(sondear, 5000);
})();