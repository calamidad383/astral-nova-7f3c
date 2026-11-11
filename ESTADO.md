# ESTADO del proyecto

## Estado actual: MVP ampliado (motor de IA local + panel del dueño + ciberseguridad)

### Hecho
- [x] Estructura del repositorio: `bot/`, `api/`, `ia/`, `app/`, `docs/`, `docker/`, `tests/`, `.github/workflows/`
- [x] `LICENSE` (MIT), `PRIVACY.md`, `SECURITY.md`, `CONTRIBUTING.md`, `.env.example`, `.gitignore`
- [x] **IA local y autocontenida** (`ia/motor.py`): sin APIs externas ni claves. Índice TF-IDF sobre la base de conocimiento de cada servidor, aprendizaje por retroalimentación persistido en SQLite (`ia_aprendizaje`), clasificador de toxicidad con normalización leetspeak, patrones anti-scam, clasificador de intenciones admin, plantillas de comunidad (gaming/academia/negocio/trading/creador) y resumidor extractivo. `ia/cerebro.py` es la fachada asíncrona.
- [x] RAG con citas (`ia/rag.py`), prompts y evaluaciones (`ia/prompts.py`, `ia/evaluaciones.py`)
- [x] Constructor de servidores: validar/aplicar/deshacer, plantillas de permisos (nunca Administrador), reversible
- [x] Bot con **19 módulos**: bienvenida, moderación, anti-spam, verificación, logs, roles por botones, encuestas, tickets, `/pregunta` con citas, constructor, **niveles, sorteos, sugerencias, recordatorios, anuncios programados, backups, resúmenes, anti-nuke con cuarentena, tienda con PayPal**
- [x] **Tienda** (`bot/cogs/tienda.py` + API): productos con panel de compra por botones, códigos de descuento con límite de usos, registro de ventas; compite con Shopify para comunidades (sin web externa ni $29/mes)
- [x] **Empaquetado multiplataforma** (Tauri v2 en `src-tauri/`): releases automáticas en GitHub Actions al crear un tag `v*` — instalador de Windows, APK de Android, macOS y Linux; iOS pendiente de cuenta de desarrollador Apple; la PWA ya cubre todos los dispositivos mientras tanto
- [x] **Guía de Hostinger** (`docs/hostinger.md`) + script de instalación automática (`scripts/instalar-hostinger.sh`) con HTTPS (Caddy)
- [x] **Panel siempre encendido en GitHub Pages** (workflow `paginas.yml`): el panel se publica en https://calamidad383.github.io/astral-nova-7f3c/ con cada cambio en main
- [x] **Actualización con un clic dentro de la app**: `app/version.json` + service worker con limpieza de caché; al haber versión nueva aparece una barra "Nueva versión disponible — Actualizar ahora" (en PWA recarga sola; en APK/EXE abre la última release de GitHub)
- [x] **Ciberseguridad** (`api/seguridad.py` + escudo en `api/main.py`): bans permanentes de IP (5 logins fallidos en 15 min → ban para siempre), rate limiting, cabeceras de seguridad, registro de eventos visible en el panel, endpoint para desbanear manualmente
- [x] **Panel de negocio del dueño**: tabla `pagos`, `/negocio/resumen` (ingresos, ventas, reembolsos, neto, por plan, transacciones; modo ejemplo si no hay PayPal), `/negocio/pago` manual, webhook PayPal registra pagos reales
- [x] **Sincronización PayPal SIN webhooks** (`/negocio/sincronizar-paypal` + botón en el panel): consulta la API de transacciones de PayPal con las credenciales y registra pagos/reembolsos reales con deduplicación — verificado en vivo contra sandbox; no necesita dominio ni URL pública
- [x] **Panel del dueño protegido con contraseña** (`PANEL_PASSWORD`, por defecto `Shadow`): los endpoints de negocio y seguridad exigen la clave; la app muestra candado y se desbloquea con un input
- [x] **APK universal con las 4 arquitecturas** (arm64, armv7 32 bits, x86, x86_64): compatible con todos los teléfonos existentes, incluidos los que corren Android en 32 bits (ej. ZTE Blade A36)
- [x] **Login con Discord reparado**: el botón no tenía Client ID ni existía la página de retorno; ahora hay `app/callback.html` (intercambia el código por sesión, guarda token en PWA y muestra código de acceso para pegar en el APK), `redirect_uri` fijo de GitHub Pages y campo para pegar el código en la app. Requiere añadir la URL de callback en el portal de Discord y el servidor en línea
- [x] **PWA con pestaña Negocio**: cifras de ingresos/ventas/reembolsos/neto, desglose por plan, últimas transacciones y resumen de seguridad; instalable en Android/iOS/escritorio (manifest + service worker)
- [x] API FastAPI completa (auth OAuth2, servidores, constructor, módulos, conocimiento, analíticas, facturación, webhook PayPal con verificación de firma, negocio, seguridad)
- [x] Docker (bot + API) y CI en GitHub Actions (pytest + verificación de la PWA)
- [x] Pruebas: 32 tests (`tests/test_fase1.py` + `tests/test_motor_local.py` + `tests/test_tienda.py`): constructor, RAG, motor local, seguridad y ciclo completo de tienda
- [x] `README.md` original (guía v3+V4) eliminado según instrucción del dueño; la siguiente especificación llegará como archivo nuevo que se leerá completo

### Credenciales recibidas (guardadas SOLO en `.env`, fuera de git)
- [x] DISCORD_TOKEN verificado contra la API de Discord (bot: NEXO, id 1553129631287218236)
- [x] PayPal client_id/secret verificados: son de SANDBOX (entorno de pruebas); PAYPAL_BASE apuntado a sandbox
- [x] DISCORD_CLIENT_ID + DISCORD_CLIENT_SECRET verificados contra OAuth2 (200) — login del panel listo
- [x] Distribución decidida: las apps se descargarán desde GitHub Releases por dispositivo (Android/iOS/escritorio); cuenta de desarrollador Apple/Google aplazada hasta que el dueño pague

### Pendiente
- [ ] **Sección 2 de la app**: esperando archivo nuevo que subirá el dueño al repositorio (se leerá completito y todo su contenido será la actualización a aplicar)
- [ ] Faltan del dueño: decisión de hosting (Hostinger de pago u Oracle Cloud gratis) y dominio opcional; el Webhook ID ya NO es necesario (hay sincronización directa)
- [ ] Archivo "Mira la instrucción" subido a main pero VACÍO: esperando contenido (será la sección 2 de la app)
- [ ] Recomendado: rotar el token de Discord y el secreto de PayPal (se compartieron por chat)
- [ ] Conectar API ↔ bot por cola de tareas: aplicar/deshacer desde el panel
- [ ] Empaquetado de escritorio/móvil nativo (la PWA ya es instalable; empaquetar con Tauri/Flutter si se quiere binario para Windows)
- [ ] PayPal real: crear suscripciones con plan_id reales cuando el dueño entregue credenciales
- [ ] Búsqueda semántica con vectores en el RAG

### Problemas encontrados y resueltos
- `BaseDatos` con aiosqlite: `row_factory` debe fijarse dentro del `async with`.
- `MotorLocal.aprender()` escribía en una tabla que solo se creaba en `entrenar()` → tabla asegurada en ambos caminos.
- `/negocio/resumen` perdía el campo `modo` al reconsultar tras sembrar datos de ejemplo → corregido.
- `extraer_json`/`plan_por_defecto` se perdieron al reescribir `cerebro.py` → restauradas.

### Auditoría v0.3.x (2026-11-11) — app revisada a fondo
- Login con Discord: cambio a OAuth2 implícito (`response_type=token`) — **no requiere servidor**; `callback.html` en GitHub Pages entrega el token y código de acceso para la APK.
- **Modo local**: la app funciona completa sin servidor (módulos con persistencia local, constructor IA portado a JS con las 5 plantillas, documentos, negocio con datos de ejemplo marcados); la dirección del servidor se configura en Cuenta.
- Manifest reparado (`start_url: "./"` + `scope: "./"` — antes la PWA instalada era inaccesible en la subruta de GitHub Pages) + iconos PNG 192/512.
- Service worker: solo mismo origen y red-primero (antes cacheaba respuestas de Discord y servía contenido viejo).
- Móvil: barra de pestañas fija inferior con safe-area, botones a ancho completo, inputs 16px (evita zoom en iOS), topbar con ajuste de línea.
- Marca unificada a NEXO (título, topbar, manifest); pie con versión dinámica.
- Cuenta: cerrar sesión + campo de servidor de datos; expiración del token de Discord (7 días) detectada → re-login.
- Tauri: plugin `opener` + `withGlobalTauri` — "Actualizar ahora" y el login abren el navegador del sistema (antes `window.open` no hacía nada en la APK).
- GitHub Pages publicado (Source: GitHub Actions, activado por el dueño) y despliegue automático en cada push a main.
- Publicado: v0.3.0 y v0.3.1 (login en navegador del sistema) — APK universal + Windows + macOS + Linux.

### Regla de este archivo
Actualizarlo en cada unidad de trabajo: qué se hizo, qué queda, qué problemas.
