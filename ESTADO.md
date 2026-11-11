# ESTADO del proyecto

## Estado actual: MVP ampliado (motor de IA local + panel del dueño + ciberseguridad)

### Hecho
- [x] Estructura del repositorio: `bot/`, `api/`, `ia/`, `app/`, `docs/`, `docker/`, `tests/`, `.github/workflows/`
- [x] `LICENSE` (MIT), `PRIVACY.md`, `SECURITY.md`, `CONTRIBUTING.md`, `.env.example`, `.gitignore`
- [x] **IA local y autocontenida** (`ia/motor.py`): sin APIs externas ni claves. Índice TF-IDF sobre la base de conocimiento de cada servidor, aprendizaje por retroalimentación persistido en SQLite (`ia_aprendizaje`), clasificador de toxicidad con normalización leetspeak, patrones anti-scam, clasificador de intenciones admin, plantillas de comunidad (gaming/academia/negocio/trading/creador) y resumidor extractivo. `ia/cerebro.py` es la fachada asíncrona.
- [x] RAG con citas (`ia/rag.py`), prompts y evaluaciones (`ia/prompts.py`, `ia/evaluaciones.py`)
- [x] Constructor de servidores: validar/aplicar/deshacer, plantillas de permisos (nunca Administrador), reversible
- [x] Bot con **18 módulos**: bienvenida, moderación, anti-spam, verificación, logs, roles por botones, encuestas, tickets, `/pregunta` con citas, constructor, **niveles, sorteos, sugerencias, recordatorios, anuncios programados, backups, resúmenes, anti-nuke con cuarentena**
- [x] **Ciberseguridad** (`api/seguridad.py` + escudo en `api/main.py`): bans permanentes de IP (5 logins fallidos en 15 min → ban para siempre), rate limiting, cabeceras de seguridad, registro de eventos visible en el panel, endpoint para desbanear manualmente
- [x] **Panel de negocio del dueño**: tabla `pagos`, `/negocio/resumen` (ingresos, ventas, reembolsos, neto, por plan, transacciones; modo ejemplo si no hay PayPal), `/negocio/pago` manual, webhook PayPal registra pagos reales
- [x] **PWA con pestaña Negocio**: cifras de ingresos/ventas/reembolsos/neto, desglose por plan, últimas transacciones y resumen de seguridad; instalable en Android/iOS/escritorio (manifest + service worker)
- [x] API FastAPI completa (auth OAuth2, servidores, constructor, módulos, conocimiento, analíticas, facturación, webhook PayPal con verificación de firma, negocio, seguridad)
- [x] Docker (bot + API) y CI en GitHub Actions (pytest + verificación de la PWA)
- [x] Pruebas: 30 tests (`tests/test_fase1.py` + `tests/test_motor_local.py`): constructor, RAG, motor local (preguntas con citas, moderación, planes, resúmenes, aprendizaje persistente) y seguridad (ban permanente)
- [x] `README.md` original (guía v3+V4) eliminado según instrucción del dueño; la siguiente especificación llegará como archivo nuevo que se leerá completo

### Pendiente
- [ ] **Sección 2 de la app**: esperando archivo nuevo que subirá el dueño al repositorio (se leerá completito y todo su contenido será la actualización a aplicar)
- [ ] Conectar API ↔ bot por cola de tareas: aplicar/deshacer desde el panel
- [ ] Empaquetado de escritorio/móvil nativo (la PWA ya es instalable; empaquetar con Tauri/Flutter si se quiere binario para Windows)
- [ ] PayPal real: crear suscripciones con plan_id reales cuando el dueño entregue credenciales
- [ ] Búsqueda semántica con vectores en el RAG

### Problemas encontrados y resueltos
- `BaseDatos` con aiosqlite: `row_factory` debe fijarse dentro del `async with`.
- `MotorLocal.aprender()` escribía en una tabla que solo se creaba en `entrenar()` → tabla asegurada en ambos caminos.
- `/negocio/resumen` perdía el campo `modo` al reconsultar tras sembrar datos de ejemplo → corregido.
- `extraer_json`/`plan_por_defecto` se perdieron al reescribir `cerebro.py` → restauradas.

### Regla de este archivo
Actualizarlo en cada unidad de trabajo: qué se hizo, qué queda, qué problemas.
