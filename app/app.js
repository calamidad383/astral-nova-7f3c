
const VERSION_APP = "0.2.4";
const URL_VERSIONES = "https://calamidad383.github.io/astral-nova-7f3c/version.json";
const URL_RELEASES = "https://github.com/calamidad383/astral-nova-7f3c/releases/latest";

function versionMasNueva(a, b) {
  const pa = a.split(".").map(Number), pb = b.split(".").map(Number);
  for (let i = 0; i < 3; i++) {
    if ((pb[i] || 0) > (pa[i] || 0)) return true;
    if ((pb[i] || 0) < (pa[i] || 0)) return false;
  }
  return false;
}

async function revisarActualizacion() {
  try {
    const r = await fetch(URL_VERSIONES + "?t=" + Date.now());
    const datos = await r.json();
    if (!versionMasNueva(VERSION_APP, datos.version)) return;
    $("#notas-version").textContent = datos.notas || "";
    $("#aviso-actualizacion").classList.remove("oculto");
  } catch {}
}

function actualizarAhora() {
  localStorage.setItem("version_app", VERSION_APP);
  if (navigator.serviceWorker && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage("actualizar");
    setTimeout(() => location.reload(), 500);
  } else {
    window.open(URL_RELEASES, "_blank");
  }
}

const API = localStorage.getItem("api_url") || "http://localhost:8000";
const TOKEN = localStorage.getItem("token");
const NOMBRES_MODULOS = {
  bienvenida: "Bienvenida y despedida",
  moderacion: "Moderación base",
  anti_spam: "Anti-spam",
  verificacion: "Verificación",
  logs: "Registros",
  roles_botones: "Roles por botones",
  encuestas: "Encuestas",
  tickets: "Tickets",
  pregunta: "IA /pregunta",
  constructor: "Constructor con IA",
  niveles: "Niveles y XP",
  sorteos: "Sorteos",
  sugerencias: "Sugerencias",
  recordatorios: "Recordatorios",
  anuncios: "Anuncios programados",
  backups: "Backups del servidor",
  resumenes: "Resúmenes de chat",
  anti_nuke: "Anti-nuke (cuarentena)",
  tienda: "Tienda (PayPal)",
};

const $ = (sel) => document.querySelector(sel);

function mostrar(vista) {
  for (const id of ["vista-login", "vista-panel"]) {
    document.getElementById(id).classList.toggle("oculto", id !== vista);
  }
}

const CLAVE_PANEL = localStorage.getItem("clave_panel") || "";

async function api(ruta, opciones = {}) {
  const r = await fetch(API + ruta, {
    ...opciones,
    headers: {
      "Content-Type": "application/json",
      ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
      ...(CLAVE_PANEL ? { "X-Panel-Clave": CLAVE_PANEL } : {}),
      ...(opciones.headers || {}),
    },
  });
  if (!r.ok) {
    if (r.status === 401 && ruta.startsWith("/negocio")) {
      document.getElementById("candado-panel").classList.remove("oculto");
    }
    throw new Error(`${r.status} ${await r.text()}`);
  }
  return r.json();
}

function desbloquearPanel() {
  const clave = document.getElementById("clave-panel").value;
  if (!clave) return alert("Escribe la contraseña del panel.");
  localStorage.setItem("clave_panel", clave);
  location.reload();
}

async function revisarEstado() {
  const pill = $("#estado-api");
  try {
    const estado = await api("/estado");
    pill.textContent = estado.ia_disponible ? "API lista · IA activa" : "API lista · IA sin configurar";
    $("#estado-detalle").textContent = estado.ia_disponible
      ? "API y Gemini conectados."
      : "API funcionando. Añade GEMINI_API_KEY en el servidor para activar la IA (el RAG con citas funciona igual).";
  } catch {
    pill.textContent = "API no disponible";
    $("#estado-detalle").textContent = "No se pudo conectar con la API en " + API;
  }
}

function pintarServidores(servidores) {
  const cont = $("#lista-servidores");
  if (!servidores.length) {
    cont.innerHTML = "<p>No administras ningún servidor con el bot aún.</p>";
    return;
  }
  cont.innerHTML = servidores
    .map((s) => `<div class="modulo-fila"><span>${s.nombre}</span><span class="pill">${s.dueno ? "dueño" : "admin"}</span></div>`)
    .join("");
}

function pintarModulos() {
  const cont = $("#lista-modulos");
  cont.innerHTML = Object.entries(NOMBRES_MODULOS)
    .map(
      ([id, nombre]) => `
      <div class="tarjeta modulo-fila" data-modulo="${id}">
        <span>${nombre}</span>
        <button class="interruptor" aria-label="Activar ${nombre}"></button>
      </div>`
    )
    .join("");
  cont.querySelectorAll(".interruptor").forEach((boton) => {
    boton.addEventListener("click", () => alternarModulo(boton));
  });
}

async function alternarModulo(boton) {
  const id = boton.closest("[data-modulo]").dataset.modulo;
  const activar = !boton.classList.contains("activo");
  const servidorId = localStorage.getItem("servidor_id") || "0";
  try {
    await api(`/servidores/${servidorId}/modulos/${id}`, {
      method: "PUT",
      body: JSON.stringify({ activo: activar }),
    });
    boton.classList.toggle("activo", activar);
  } catch (e) {
    alert("No se pudo cambiar el módulo: " + e.message);
  }
}

async function cargarModulos() {
  const servidorId = localStorage.getItem("servidor_id") || "0";
  for (const id of Object.keys(NOMBRES_MODULOS)) {
    try {
      const datos = await api(`/servidores/${servidorId}/modulos/${id}`);
      const fila = document.querySelector(`[data-modulo="${id}"] .interruptor`);
      if (fila) fila.classList.toggle("activo", datos.activo);
    } catch { /* sin sesión: se muestran apagados */ }
  }
}

async function cargarDocs() {
  const servidorId = localStorage.getItem("servidor_id") || "0";
  try {
    const datos = await api(`/servidores/${servidorId}/conocimiento`);
    $("#lista-docs").innerHTML = datos.documentos
      .map((d) => `<li><strong>${d.titulo}</strong> <span class="pill">${d.id}</span></li>`)
      .join("") || "<li>Sin documentos todavía.</li>";
  } catch {
    $("#lista-docs").innerHTML = "<li>Inicia sesión para ver tus documentos.</li>";
  }
}

async function proponerPlan() {
  const descripcion = $("#descripcion-comunidad").value.trim();
  if (!descripcion) return alert("Describe primero tu comunidad.");
  const servidorId = localStorage.getItem("servidor_id") || "0";
  $("#plan-resultado").textContent = "Pidiendo plan a la IA…";
  try {
    const datos = await api(`/servidores/${servidorId}/constructor/plan`, {
      method: "POST",
      body: JSON.stringify({ descripcion }),
    });
    const plan = datos.plan;
    const lineas = ["Roles:"];
    plan.roles.forEach((r) => lineas.push(`  • ${r.nombre} (${r.plantilla})`));
    lineas.push("Canales:");
    plan.categorias.forEach((c) =>
      lineas.push(`  📁 ${c.nombre}: ${c.canales.map((x) => x.nombre).join(", ")}`)
    );
    lineas.push(`Módulos: ${plan.modulos.join(", ")}`);
    lineas.push("", "En Discord usa /construir-aplicar para crearlo o /construir-deshacer para revertir.");
    $("#plan-resultado").textContent = lineas.join("\n");
    $("#estructura").textContent = plan.categorias
      .map((c) => `📁 ${c.nombre}\n` + c.canales.map((x) => `   # ${x.nombre}`).join("\n"))
      .join("\n");
  } catch (e) {
    $("#plan-resultado").textContent = "Error: " + e.message;
  }
}

async function cargarNegocio() {
  try {
    const res = await api("/negocio/resumen");
    $("#neg-ingresos").textContent = "$" + res.ingresos_totales.toFixed(2);
    $("#neg-ventas").textContent = res.ventas;
    $("#neg-reembolsos").textContent = "$" + res.reembolsos.toFixed(2);
    $("#neg-neto").textContent = "$" + res.neto.toFixed(2);
    const planes = $("#neg-planes");
    planes.innerHTML = "";
    for (const [plan, cantidad] of Object.entries(res.por_plan || {})) {
      const li = document.createElement("li");
      li.textContent = `${plan}: ${cantidad}`;
      planes.appendChild(li);
    }
    const trans = $("#neg-transacciones");
    trans.innerHTML = "";
    for (const t of res.transacciones || []) {
      const li = document.createElement("li");
      li.textContent = `${t.creado_en} · ${t.plan} · $${t.monto.toFixed(2)}${t.tipo === "reembolso" ? " (reembolso)" : ""}`;
      trans.appendChild(li);
    }
    const seg = await api("/seguridad/eventos");
    const eventos = seg.eventos || [];
    $("#seg-resumen").textContent = `${eventos.length} eventos de seguridad registrados · ${seg.bans.length} IPs baneadas permanentemente`;
    const lista = $("#seg-eventos");
    lista.innerHTML = "";
    for (const ev of eventos.slice(0, 10)) {
      const li = document.createElement("li");
      li.textContent = `${ev.creado_en} · ${ev.tipo} · ${ev.ip || "-"}`;
      lista.appendChild(li);
    }
  } catch (e) {
    $("#seg-resumen").textContent = "No disponible: " + e.message;
  }
}

async function sincronizarPayPal() {
  const salida = $("#sincro-resultado");
  salida.textContent = "Sincronizando…";
  try {
    const r = await api("/negocio/sincronizar-paypal", { method: "POST" });
    salida.textContent = `✅ ${r.nuevos} nuevas · cobrado $${r.cobrado.toFixed(2)} · devuelto $${r.devuelto.toFixed(2)}`;
    cargarNegocio();
  } catch (e) {
    salida.textContent = "No se pudo sincronizar: " + e.message;
  }
}

async function añadirDoc() {
  const titulo = $("#doc-titulo").value.trim();
  const contenido = $("#doc-contenido").value.trim();
  if (!titulo || !contenido) return alert("Falta título o contenido.");
  const servidorId = localStorage.getItem("servidor_id") || "0";
  try {
    await api(`/servidores/${servidorId}/conocimiento`, {
      method: "PUT",
      body: JSON.stringify({ titulo, contenido }),
    });
    $("#doc-titulo").value = "";
    $("#doc-contenido").value = "";
    cargarDocs();
  } catch (e) {
    alert("No se pudo guardar: " + e.message);
  }
}

// Navegación por pestañas
document.querySelectorAll(".tabs button").forEach((boton) => {
  boton.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach((b) => b.classList.remove("activo"));
    boton.classList.add("activo");
    document.querySelectorAll(".tab").forEach((t) => t.classList.add("oculto"));
    document.getElementById(`tab-${boton.dataset.tab}`).classList.remove("oculto");
  });
});

$("#btn-plan").addEventListener("click", proponerPlan);
$("#btn-doc").addEventListener("click", añadirDoc);

// Login: enlace OAuth2 de Discord
const CLIENT_ID = localStorage.getItem("discord_client_id") || "";
if (CLIENT_ID) {
  $("#btn-discord").href =
    `https://discord.com/oauth2/authorize?client_id=${CLIENT_ID}` +
    `&response_type=code&redirect_uri=${encodeURIComponent(location.origin + "/auth/callback.html")}` +
    `&scope=identify%20guilds`;
} else {
  $("#btn-discord").href = "#";
  $("#btn-discord").addEventListener("click", () =>
    alert("Configura DISCORD_CLIENT_ID en la API. Ver docs/despliegue.md")
  );
}

if (TOKEN) {
  mostrar("vista-panel");
  pintarModulos();
  revisarEstado();
  cargarModulos();
  cargarDocs();
  cargarNegocio();
  document.getElementById("btn-sincronizar").addEventListener("click", sincronizarPayPal);
  document.getElementById("btn-actualizar").addEventListener("click", actualizarAhora);
  revisarActualizacion();
} else {
  mostrar("vista-login");
  revisarEstado();
}
