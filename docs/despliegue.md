# Despliegue

## 1. Local (desarrollo)

```bash
cp .env.example .env        # rellena DISCORD_TOKEN y GEMINI_API_KEY como mínimo
python -m venv .venv && source .venv/bin/activate
pip install -r bot/requirements.txt -r api/requirements.txt -r tests/requirements.txt
uvicorn api.main:app --reload          # terminal 1: API en http://localhost:8000
python -m bot.main                     # terminal 2: bot
python -m http.server 8080 -d app      # terminal 3: PWA en http://localhost:8080
```

## 2. Crear el bot en Discord (lo haces tú a mano)

1. En el [portal de desarrolladores](https://discord.com/developers/applications): New Application → Bot. Copia el token a `DISCORD_TOKEN`.
2. OAuth2 → añade el redirect `http://localhost:8000/auth/discord/callback` (y el de producción).
3. Invita al bot con los permisos **Gestionar roles** y **Gestionar canales** (sin Administrador):
   `https://discord.com/oauth2/authorize?client_id=TU_CLIENT_ID&permissions=268445696&scope=bot%20applications.commands`
4. Activa los *intents* privileged: **Server Members** y **Message Content**.

## 3. Producción con Docker

```bash
cp .env.example .env    # rellena TODO, incluido PAYPAL_*
cd docker && docker compose up -d --build
```

- La API queda en el puerto 8000; ponle HTTPS con un proxy (Caddy/Nginx).
- La PWA se sirve desde GitHub Pages o desde el mismo proxy.
- La base de datos vive en `data/` (monta un volumen o migra a PostgreSQL en fase 4).

## 4. PayPal (sección 10 de la guía)

1. Cuenta Business → developer.paypal.com → app Sandbox → copia Client ID y Secret.
2. Crea Producto + Planes de suscripción (Pro $8, Business $30) → copia los `plan_id`.
3. Webhook hacia `https://TU_DOMINIO/paypal/webhook` con los eventos de suscripción → copia el Webhook ID.
4. Guarda todo en `.env` y prueba en Sandbox antes de pasar a Live.

## 5. Publicar la PWA en GitHub Pages

La PWA es estática (`app/`). Configura Pages para servir la carpeta `app/` de la rama que elijas. En `app/app.js`, ajusta `api_url` apuntando al dominio de la API con HTTPS.
