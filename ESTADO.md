# ESTADO del proyecto

## Fase 1 — MVP (en curso)

### Hecho
- [x] Estructura del repositorio (sección 12 de la guía): `bot/`, `api/`, `ia/`, `app/`, `docs/`, `docker/`, `tests/`, `.github/workflows/`
- [x] `README.md` con la guía completa (v3 + Parte V4 con análisis competitivo)
- [x] `LICENSE` (MIT), `PRIVACY.md`, `SECURITY.md`, `CONTRIBUTING.md`, `.env.example`, `.gitignore`
- [x] Capa de IA: `ia/cerebro.py` (Gemini por API REST, modo sin-IA con degradación), `ia/rag.py` (RAG con citas), `ia/prompts.py`, `ia/evaluaciones.py`
- [x] Constructor de servidores: `bot/constructor.py` (validar/aplicar/deshacer, plantillas de permisos, sin Administrador)
- [x] Bot núcleo: `bot/main.py`, `bot/config.py`, `bot/db.py`
- [x] Cogs fase 1: bienvenida, moderación, anti-spam, verificación, logs, roles por botones, encuestas (API de polls), tickets, `/pregunta` con citas, constructor (`/construir`, `/construir-aplicar`, `/construir-deshacer`)
- [x] API FastAPI: `/estado`, `/auth/discord`, `/servidores`, constructor (plan/aplicar/deshacer), módulos, conocimiento, analíticas básicas, `/facturacion/suscribir`, `/paypal/webhook` con verificación de firma
- [x] PWA en `app/`: login Discord OAuth2, selector de servidores, constructor con vista previa, base de conocimiento, interruptores de módulos, plan y privacidad; instalable (manifest + service worker)
- [x] Docker (bot + API con docker-compose) y CI en GitHub Actions (pytest + verificación de la PWA)
- [x] Pruebas: `tests/test_fase1.py` (constructor, plan por defecto, RAG con citas, evaluaciones estructurales)

### Pendiente (siguiente paso)
- [ ] Conectar API ↔ bot por cola de tareas (fase 2): aplicar/deshacer desde el panel
- [ ] Analíticas reales (fase 2): crecimiento, retención, resúmenes automáticos
- [ ] Anti-raid, anti-nuke IA, niveles, sorteos, sugerencias (fase 2)
- [ ] Vectores y búsqueda semántica en el RAG (fase 2)
- [ ] App Flutter (Android/escritorio) y flujo de Releases con hashes SHA-256
- [ ] PayPal: completar creación de suscripciones con plan_id reales
- [ ] Logo final y capturas para el README

### Problemas encontrados
- Ninguno por ahora.

### Regla de este archivo
Actualizarlo en cada unidad de trabajo: qué se hizo, qué queda, qué problemas.
