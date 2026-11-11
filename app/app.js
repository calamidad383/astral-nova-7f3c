const VERSION_APP = "0.3.0";
const URL_VERSIONES = "https://calamidad383.github.io/astral-nova-7f3c/version.json";
const URL_RELEASES = "https://github.com/calamidad383/astral-nova-7f3c/releases/latest";

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

function lsGet(clave, defecto) {
  try {
    const v = localStorage.getItem(clave);
    return v === null ? defecto : JSON.parse(v);
  } catch {
    return defecto;
  }
}

function lsSet(clave, valor) {
  try { localStorage.setItem(clave, JSON.stringify(valor)); } catch {}
}

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

async function actualizarAhora() {
  localStorage.setItem("version_app", VERSION_APP);
  const tauri = window.__TAURI__;
  if (tauri && tauri.opener && tauri.opener.openUrl) {
    try { await tauri.opener.openUrl(URL_RELEASES); return; } catch {}
  }
  if (navigator.serviceWorker && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage("actualizar");
    setTimeout(() => location.reload(), 500);
    return;
  }
  window.open(URL_RELEASES, "_blank");
}

// ── Modo de operación: "conectado" (con servidor) o "local" (todo en el teléfono) ──
const API = (localStorage.getItem("api_url") || "").replace(/\/+$/, "").replace(/^"|"$/g, "");
const TOKEN = localStorage.getItem("token");
let MODO = API ? "conectando" : "local";

function mostrar(vista) {
  for (const id of ["vista-login", "vista-panel"]) {
    document.getElementById(id).classList.toggle("oculto", id !== vista);
  }
}

function pintarModo() {
  const pill = $("#estado-api");
  if (MODO === "conectado") {
    pill.textContent = "🟢 Conectado al servidor";
  } else if (MODO === "local") {
    pill.textContent = "📱 Modo local";
  } else {
    pill.textContent = "conectando…";
  }
}

const CLAVE_PANEL = (localStorage.getItem("clave_panel") || "").replace(/^"|"$/g, "");

async function api(ruta, opciones = {}) {
  const controlador = new AbortController();
  const tiempo = setTimeout(() => controlador.abort(), 6000);
  let r;
  try {
    r = await fetch(API + ruta, {
      ...opciones,
      signal: controlador.signal,
      headers: {
        "Content-Type": "application/json",
        ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
        ...(CLAVE_PANEL ? { "X-Panel-Clave": CLAVE_PANEL } : {}),
        ...(opciones.headers || {}),
      },
    });
  } finally {
    clearTimeout(tiempo);
  }
  if (!r.ok) {
    if (r.status === 401 && (ruta.startsWith("/negocio") || ruta.startsWith("/seguridad"))) {
      document.getElementById("candado-panel").classList.remove("oculto");
    }
    throw new Error(`${r.status} ${await r.text()}`);
  }
  return r.json();
}

async function revisarEstado() {
  pintarModo();
  const detalle = $("#estado-detalle");
  if (!API) {
    MODO = "local";
    pintarModo();
    detalle.innerHTML = "<strong>Modo local activo:</strong> la app funciona completa en tu teléfono. " +
      "Cuando quieras datos en vivo (ventas reales, el bot en tu servidor), escribe la dirección del servidor en la pestaña <em>Cuenta</em>.";
    return;
  }
  try {
    const estado = await api("/estado");
    MODO = "conectado";
    pintarModo();
    detalle.textContent = "Conectado al servidor. IA lista: " + (estado.ia_disponible ? "sí" : "pendiente") + ".";
  } catch {
    MODO = "local";
    pintarModo();
    detalle.innerHTML = "No se pudo conectar con el servidor (<code>" + API + "</code>). " +
      "La app sigue funcionando en <strong>modo local</strong>. Revisa la dirección en la pestaña <em>Cuenta</em>.";
  }
}

// ── Servidores ──
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

async function cargarServidores() {
  if (MODO !== "conectado") {
    $("#lista-servidores").innerHTML =
      "<p>En modo local no hay servidores conectados.</p><p class=\"nota\">Invita al bot NEXO a tu servidor de Discord y conecta un servidor de datos (pestaña Cuenta) para verlos aquí.</p>";
    return;
  }
  try {
    pintarServidores(await api("/servidores"));
  } catch (e) {
    $("#lista-servidores").innerHTML = "<p>No se pudo cargar: " + e.message + "</p>";
  }
}

// ── Módulos ──
function pintarModulos() {
  const cont = $("#lista-modulos");
  const estado = lsGet("modulos_local", {});
  cont.innerHTML = Object.entries(NOMBRES_MODULOS)
    .map(
      ([id, nombre]) => `
      <div class="tarjeta modulo-fila" data-modulo="${id}">
        <span>${nombre}</span>
        <button class="interruptor ${estado[id] ? "activo" : ""}" aria-label="Activar ${nombre}"></button>
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
  if (MODO !== "conectado") {
    const estado = lsGet("modulos_local", {});
    estado[id] = activar;
    lsSet("modulos_local", estado);
    boton.classList.toggle("activo", activar);
    return;
  }
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
  if (MODO !== "conectado") return;
  const servidorId = localStorage.getItem("servidor_id") || "0";
  for (const id of Object.keys(NOMBRES_MODULOS)) {
    try {
      const datos = await api(`/servidores/${servidorId}/modulos/${id}`);
      const fila = document.querySelector(`[data-modulo="${id}"] .interruptor`);
      if (fila) fila.classList.toggle("activo", datos.activo);
    } catch { /* se muestran apagados */ }
  }
}

// ── Base de conocimiento (funciona también en modo local) ──
function docsLocales() {
  return lsGet("documentos_local", []);
}

async function cargarDocs() {
  const lista = $("#lista-docs");
  if (MODO !== "conectado") {
    const docs = docsLocales();
    lista.innerHTML = docs.length
      ? docs.map((d) => `<li><strong>${d.titulo}</strong> <span class="pill">guardado en tu teléfono</span></li>`).join("")
      : "<li>Sin documentos todavía. Añade el primero abajo.</li>";
    return;
  }
  const servidorId = localStorage.getItem("servidor_id") || "0";
  try {
    const datos = await api(`/servidores/${servidorId}/conocimiento`);
    lista.innerHTML = datos.documentos
      .map((d) => `<li><strong>${d.titulo}</strong> <span class="pill">${d.id}</span></li>`)
      .join("") || "<li>Sin documentos todavía.</li>";
  } catch {
    lista.innerHTML = "<li>No se pudo cargar la lista del servidor.</li>";
  }
}

async function añadirDoc() {
  const titulo = $("#doc-titulo").value.trim();
  const contenido = $("#doc-contenido").value.trim();
  if (!titulo || !contenido) return alert("Falta título o contenido.");
  if (MODO !== "conectado") {
    const docs = docsLocales();
    docs.push({ id: "local-" + Date.now(), titulo, contenido });
    lsSet("documentos_local", docs);
    $("#doc-titulo").value = "";
    $("#doc-contenido").value = "";
    cargarDocs();
    return;
  }
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

// ── Constructor con IA (funciona también en modo local) ──
const PLANTILLAS = {
  gaming: {
    claves: ["gaming", "juego", "juegos", "clan", "esports", "valorant", "minecraft", "fortnite", "roblox"],
    roles: [["Dueño de clan", "#EF4444", "moderador"], ["Jugador", "#5865F2", "miembro"], ["Espectador", "#9AA0B4", "miembro"]],
    categorias: [
      ["GENERAL", [["bienvenida", "texto", true], ["reglas", "texto", true], ["anuncios", "texto", true]]],
      ["JUEGOS", [["general", "texto", false], ["clips-y-momentos", "texto", false], ["busco-equipo", "texto", false], ["sala-de-juego", "voz", false]]],
      ["SOPORTE", [["tickets", "texto", false]]],
    ],
    modulos: ["bienvenida", "tickets", "anti_spam", "niveles", "encuestas", "roles_botones"],
  },
  academia: {
    claves: ["academia", "curso", "cursos", "clase", "clases", "estudio", "estudiar", "ingles", "inglés", "aprender", "educativo", "escuela", "tutoria"],
    roles: [["Profesor", "#F59E0B", "moderador"], ["Estudiante", "#5865F2", "miembro"], ["Ayudante", "#22C55E", "moderador"]],
    categorias: [
      ["INFORMACIÓN", [["bienvenida", "texto", true], ["reglas", "texto", true], ["horarios", "texto", true]]],
      ["CLASES", [["general", "texto", false], ["tareas", "texto", false], ["dudas", "texto", false], ["sala-de-practica", "voz", false]]],
      ["SOPORTE", [["tickets", "texto", false]]],
    ],
    modulos: ["bienvenida", "tickets", "anti_spam", "pregunta", "encuestas", "recordatorios"],
  },
  negocio: {
    claves: ["tienda", "negocio", "venta", "vender", "clientes", "servicio", "productos", "compra"],
    roles: [["Cliente VIP", "#F59E0B", "miembro"], ["Cliente", "#5865F2", "miembro"], ["Atención", "#22C55E", "moderador"]],
    categorias: [
      ["TIENDA", [["bienvenida", "texto", true], ["catalogo", "texto", true], ["ofertas", "texto", true]]],
      ["ATENCIÓN", [["dudas", "texto", false], ["tickets", "texto", false], ["sala-de-reunion", "voz", false]]],
    ],
    modulos: ["bienvenida", "tickets", "anti_spam", "encuestas", "anuncios"],
  },
  trading: {
    claves: ["trading", "trader", "bolsa", "inversion", "inversión", "finanzas", "educacion financiera"],
    roles: [["Mentor", "#F59E0B", "moderador"], ["Alumno Pro", "#22C55E", "miembro"], ["Alumno", "#5865F2", "miembro"]],
    categorias: [
      ["INFORMACIÓN", [["bienvenida", "texto", true], ["reglas", "texto", true], ["disclaimer-educativo", "texto", true]]],
      ["COMUNIDAD", [["general", "texto", false], ["dudas-educativas", "texto", false], ["biblioteca", "texto", false], ["sala-de-estudio", "voz", false]]],
      ["SOPORTE", [["tickets", "texto", false]]],
    ],
    modulos: ["bienvenida", "tickets", "anti_spam", "pregunta", "niveles", "anuncios"],
  },
  creador: {
    claves: ["creador", "streamer", "twitch", "youtube", "contenido", "fans", "suscriptores"],
    roles: [["Suscriptor VIP", "#7C5CFF", "miembro"], ["Fan", "#5865F2", "miembro"], ["Moderador de live", "#22C55E", "moderador"]],
    categorias: [
      ["CANAL", [["bienvenida", "texto", true], ["reglas", "texto", true], ["anuncios-de-directo", "texto", true]]],
      ["COMUNIDAD", [["general", "texto", false], ["fan-art", "texto", false], ["sugerencias", "texto", false], ["sala-del-directo", "voz", false]]],
    ],
    modulos: ["bienvenida", "anti_spam", "niveles", "roles_botones", "anuncios"],
  },
};

const PLANTILLA_GENERAL = {
  roles: [["Moderador", "#F59E0B", "moderador"], ["Miembro", "#5865F2", "miembro"]],
  categorias: [
    ["INFORMACIÓN", [["bienvenida", "texto", true], ["reglas", "texto", true], ["anuncios", "texto", true]]],
    ["GENERAL", [["general", "texto", false], ["soporte", "texto", false]]],
  ],
  modulos: ["bienvenida", "tickets", "anti_spam", "encuestas"],
};

function planLocal(descripcion) {
  const texto = descripcion.toLowerCase();
  let mejor = 0, tipo = null;
  for (const [nombre, datos] of Object.entries(PLANTILLAS)) {
    const coincidencias = datos.claves.filter((c) => texto.includes(c)).length;
    if (coincidencias > mejor) { tipo = nombre; mejor = coincidencias; }
  }
  const plantilla = tipo ? PLANTILLAS[tipo] : PLANTILLA_GENERAL;
  let roles = plantilla.roles.map(([n, c, p]) => ({ nombre: n, color: c, plantilla: p }));
  let modulos = [...plantilla.modulos];
  if (/(vip|pago|suscripcion|suscripción)/.test(texto)) {
    roles = roles.concat([{ nombre: "VIP", color: "#7C5CFF", plantilla: "miembro" }]);
    if (!modulos.includes("anuncios")) modulos.push("anuncios");
  }
  return {
    tipo: tipo || "general",
    roles,
    categorias: plantilla.categorias.map(([nombre, canales]) => ({
      nombre,
      canales: canales.map(([cn, tp, sl]) => ({ nombre: cn, tipo: tp, solo_lectura: sl })),
    })),
    modulos,
  };
}

function pintarPlan(plan) {
  const lineas = ["Roles:"];
  plan.roles.forEach((r) => lineas.push(`  • ${r.nombre} (${r.plantilla})`));
  lineas.push("Canales:");
  plan.categorias.forEach((c) =>
    lineas.push(`  📁 ${c.nombre}: ${c.canales.map((x) => x.nombre).join(", ")}`)
  );
  lineas.push(`Módulos: ${plan.modulos.map((m) => NOMBRES_MODULOS[m] || m).join(", ")}`);
  lineas.push("", "En Discord usa /construir-aplicar para crearlo o /construir-deshacer para revertir.");
  $("#plan-resultado").textContent = lineas.join("\n");
  $("#estructura").textContent = plan.categorias
    .map((c) => `📁 ${c.nombre}\n` + c.canales.map((x) => `   # ${x.nombre}`).join("\n"))
    .join("\n");
}

async function proponerPlan() {
  const descripcion = $("#descripcion-comunidad").value.trim();
  if (!descripcion) return alert("Describe primero tu comunidad.");
  $("#plan-resultado").textContent = "Creando plan con la IA…";
  if (MODO !== "conectado") {
    const plan = planLocal(descripcion);
    lsSet("ultimo_plan", plan);
    pintarPlan(plan);
    return;
  }
  const servidorId = localStorage.getItem("servidor_id") || "0";
  try {
    const datos = await api(`/servidores/${servidorId}/constructor/plan`, {
      method: "POST",
      body: JSON.stringify({ descripcion }),
    });
    lsSet("ultimo_plan", datos.plan);
    pintarPlan(datos.plan);
  } catch (e) {
    $("#plan-resultado").textContent = "Error: " + e.message;
  }
}

function pintarUltimoPlan() {
  const plan = lsGet("ultimo_plan", null);
  if (plan) pintarPlan(plan);
}

// ── Negocio (cifras reales con servidor; ejemplo claro en modo local) ──
const DATOS_EJEMPLO = {
  ingresos_totales: 1247.5,
  ventas: 89,
  reembolsos: 32.0,
  neto: 1215.5,
  por_plan: { Básico: 41, Pro: 33, Élite: 15 },
  transacciones: [
    { creado_en: "hoy", plan: "Pro", monto: 9.99, tipo: "pago" },
    { creado_en: "hoy", plan: "Élite", monto: 24.99, tipo: "pago" },
    { creado_en: "ayer", plan: "Básico", monto: 4.99, tipo: "reembolso" },
  ],
};

async function cargarNegocio() {
  const modo = $("#neg-modo");
  if (MODO !== "conectado") {
    modo.textContent = "modo ejemplo — conecta un servidor en la pestaña Cuenta para ver tus ventas reales";
    modo.classList.remove("oculto");
    pintarNegocio(DATOS_EJEMPLO);
    $("#seg-resumen").textContent = "El escudo de ciberseguridad se activa con el servidor conectado.";
    $("#seg-eventos").innerHTML = "";
    return;
  }
  modo.classList.add("oculto");
  try {
    pintarNegocio(await api("/negocio/resumen"));
  } catch (e) {
    $("#seg-resumen").textContent = "No disponible: " + e.message;
  }
  try {
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
  } catch {}
}

function pintarNegocio(res) {
  $("#neg-ingresos").textContent = "$" + (res.ingresos_totales ?? 0).toFixed(2);
  $("#neg-ventas").textContent = res.ventas ?? 0;
  $("#neg-reembolsos").textContent = "$" + (res.reembolsos ?? 0).toFixed(2);
  $("#neg-neto").textContent = "$" + (res.neto ?? 0).toFixed(2);
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
    li.textContent = `${t.creado_en} · ${t.plan} · $${Number(t.monto).toFixed(2)}${t.tipo === "reembolso" ? " (reembolso)" : ""}`;
    trans.appendChild(li);
  }
}

async function sincronizarPayPal() {
  const salida = $("#sincro-resultado");
  if (MODO !== "conectado") {
    salida.textContent = "Necesita el servidor conectado (pestaña Cuenta).";
    return;
  }
  salida.textContent = "Sincronizando…";
  try {
    const r = await api("/negocio/sincronizar-paypal", { method: "POST" });
    salida.textContent = `✅ ${r.nuevos} nuevas · cobrado $${r.cobrado.toFixed(2)} · devuelto $${r.devuelto.toFixed(2)}`;
    cargarNegocio();
  } catch (e) {
    salida.textContent = "No se pudo sincronizar: " + e.message;
  }
}

// ── Panel del dueño ──
function desbloquearPanel() {
  const clave = document.getElementById("clave-panel").value;
  if (!clave) return alert("Escribe la contraseña del panel.");
  localStorage.setItem("clave_panel", clave);
  location.reload();
}

// ── Cuenta ──
function guardarServidor() {
  const url = $("#input-servidor").value.trim().replace(/\/+$/, "");
  if (url && !/^https?:\/\//.test(url)) return alert("La dirección debe empezar por http:// o https://");
  if (url) localStorage.setItem("api_url", url);
  else localStorage.removeItem("api_url");
  location.reload();
}

function cerrarSesion() {
  localStorage.removeItem("token");
  localStorage.removeItem("usuario");
  location.reload();
}

// ── Login: OAuth2 implícito de Discord (sin servidor) ──
const CLIENT_ID = "1553129631287218236";
const REDIRECT_URI = "https://calamidad383.github.io/astral-nova-7f3c/callback.html";
$("#btn-discord").href =
  `https://discord.com/oauth2/authorize?client_id=${CLIENT_ID}` +
  `&response_type=token&redirect_uri=${encodeURIComponent(REDIRECT_URI)}` +
  `&scope=identify%20guilds`;

async function usuarioDiscord(token) {
  const r = await fetch("https://discord.com/api/v10/users/@me", {
    headers: { "Authorization": "Bearer " + token },
  });
  if (!r.ok) throw new Error("código no válido (" + r.status + ")");
  return r.json();
}

async function entrarConCodigo() {
  const codigo = $("#codigo-acceso").value.trim();
  if (!codigo) return alert("Pega el código de acceso que te dio la página de Discord.");
  try {
    const usuario = await usuarioDiscord(codigo);
    localStorage.setItem("token", codigo);
    localStorage.setItem("usuario", usuario.global_name || usuario.username);
    location.reload();
  } catch (e) {
    alert("Ese código no funciona: " + e.message + ". Inicia sesión de nuevo con Discord.");
  }
}

async function saludarUsuario() {
  const span = document.getElementById("usuario-conectado");
  if (!span || !TOKEN) return;
  const guardado = localStorage.getItem("usuario");
  if (guardado) { span.textContent = "👤 " + guardado.replace(/^"|"$/g, ""); return; }
  try {
    const usuario = await usuarioDiscord(TOKEN);
    localStorage.setItem("usuario", JSON.stringify(usuario.global_name || usuario.username));
    span.textContent = "👤 " + (usuario.global_name || usuario.username);
  } catch (e) {
    if (/\(401\)/.test(e.message)) {
      cerrarSesion();
    }
  }
}

// ── Navegación por pestañas ──
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
$("#btn-servidor-guardar").addEventListener("click", guardarServidor);
$("#btn-salir").addEventListener("click", cerrarSesion);
document.getElementById("btn-sincronizar").addEventListener("click", sincronizarPayPal);
document.getElementById("btn-actualizar").addEventListener("click", actualizarAhora);

$("#input-servidor").value = API;

if (TOKEN) {
  mostrar("vista-panel");
  const cuenta = document.getElementById("cuenta-usuario");
  if (cuenta) cuenta.textContent = (localStorage.getItem("usuario") || "Sesión iniciada").replace(/^"|"$/g, "");
  pintarModo();
  revisarEstado().then(() => {
    cargarServidores();
    cargarModulos();
    cargarDocs();
    cargarNegocio();
    pintarUltimoPlan();
  });
  saludarUsuario();
  revisarActualizacion();
} else {
  mostrar("vista-login");
  pintarModo();
  revisarEstado();
  revisarActualizacion();
}

document.getElementById("version-pie").textContent = "v" + VERSION_APP;
