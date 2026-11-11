# Despliegue en Hostinger (paso a paso, sin saber de servidores)

Objetivo: bot + API + panel funcionando 24/7 en un VPS de Hostinger con HTTPS automático.

## Opción GRATIS ($0 al mes): Oracle Cloud Always Free

Si aún no quieres pagar Hostinger, [oracle.com/cloud/free](https://www.oracle.com/cloud/free/) ofrece un VPS gratuito PARA SIEMPRE (ARM, 4 núcleos, 24 GB RAM). Mismo proceso de esta guía: Ubuntu 24.04, IP pública, y el mismo script de instalación. Los pagos NO dependen del servidor: el botón "Sincronizar PayPal" del panel trae las transacciones reales sin webhooks.

## 0. Lo que compras

1. En [hostinger.com](https://www.hostinger.com) → **VPS** → plan **KVM 1** (el más barato sirve para empezar; 4 GB de RAM es lo cómodo).
2. Al crear el VPS elige: **Ubuntu 24.04**, ubicación cercana a tus usuarios, y crea una **clave SSH** (Hostinger te la ofrece al crearlo).
3. Apunta la **IP pública** del VPS (la muestra el panel hPanel).

Opcional: un **dominio** (Hostinger los vende). Si lo compras, apunta un registro **A** hacia la IP del VPS y salta directo al paso 4 con tu dominio.

## 1. Entrar al servidor

Desde tu computadora:

```bash
ssh root@LA_IP_DE_TU_VPS
```

(Hostinger también tiene una terminal web en hPanel → VPS → Browser terminal, si prefieres no instalar nada.)

## 2. Instalación automática (un solo comando)

Sube el repositorio y ejecuta el script que hace TODO:

```bash
apt update && apt install -y git
git clone https://github.com/calamidad383/astral-nova-7f3c.git plataforma
cd plataforma
bash scripts/instalar-hostinger.sh
```

El script instala Docker, construye bot + API, configura el firewall (solo SSH, web y HTTPS abiertos) y levanta Caddy para HTTPS automático. Al final te pregunta si ya tienes dominio:

- **Con dominio**: escribes tu dominio y el certificado HTTPS se emite solo.
- **Sin dominio**: todo funciona con `http://LA_IP:8000` (suficiente para probar; para el login de Discord OAuth2 en producción conviene el dominio).

## 3. Subir las credenciales (nunca por git)

El `.env` con tus claves NO está en el repositorio (así debe ser). En tu computadora:

```bash
scp .env root@LA_IP_DE_TU_VPS:/root/plataforma/.env
```

Y reinicia: `cd plataforma/docker && docker compose restart`.

## 4. Cerrar el círculo en Discord

Con el servidor ya corriendo, en el [portal de Discord](https://discord.com/developers/applications) → tu app → **OAuth2** → Redirects, añade:

```
http://LA_IP_DE_TU_VPS:8000/auth/discord/callback        (si no hay dominio)
https://TU_DOMINIO/auth/discord/callback                 (con dominio)
```

Invita al bot: `https://discord.com/oauth2/authorize?client_id=1553129631287218236&scope=bot+applications.commands&permissions=8`

## 5. Comprobar que todo vive

```bash
cd plataforma/docker
docker compose ps          # api y bot deben estar "Up"
docker compose logs bot    # debe decir "NEXO conectado" / slash commands sincronizados
curl http://localhost:8000/estado
```

El panel se abre en `http://LA_IP:8000/app/` (o `https://TU_DOMINIO/app/`): ahí entras con tu cuenta de Discord y ves la pestaña **Negocio**.

## 6. Actualizar en el futuro

```bash
cd plataforma && git pull && cd docker && docker compose up -d --build
```

## 7. PayPal: webhooks NO son necesarios

El panel del dueño tiene el botón **"Sincronizar PayPal ahora"**: consulta la API de PayPal con tus credenciales y registra pagos y reembolsos reales sin webhook, sin dominio y sin URL pública. El webhook (`/paypal/webhook`) es opcional y solo vale la pena con dominio propio; su URL debe ser un dominio o IP válidos (por ejemplo `https://tudominio.com/paypal/webhook`), nunca un nombre suelto como `https://Carlos/...` — por eso PayPal rechazó ese intento.

## 8. Mantenimiento

- Backups: la base de datos vive en `plataforma/data/plataforma.db`; el hPanel de Hostinger permite snapshots del VPS (activa los semanales).
- Si algo falla: `docker compose logs -f` muestra el error exacto.

---

## Sobre "mi teléfono como servidor": aclaración importante

La arquitectura correcta (y la legal/estable) es:

- **El VPS de Hostinger es el cerebro**: corre el bot y la API 24/7. Es el "Hostinger de todos".
- **Tu teléfono (y los de los usuarios) son el panel**: abren la app y se conectan al VPS. Cada usuario ve SU servidor de Discord, sus datos, su plan.

Un teléfono no puede ser servidor confiable (se apaga, cambia de IP, las operadoras bloquean conexiones entrantes). Con esta arquitectura, cada teléfono se conecta "con todo el mundo" a través del VPS, que es exactly lo que quieres: tú desde tu teléfono controlas todo, y cada usuario desde el suyo controla lo suyo.
