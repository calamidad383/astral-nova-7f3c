"""API FastAPI de la plataforma (fase 1).

Endpoints (sección 9 de la guía):
- POST /auth/discord            — intercambia código OAuth2 por token y crea/actualiza usuario
- GET  /servidores              — servidores administrables del usuario
- POST /servidores/{id}/constructor/plan      — la IA propone un plan
- POST /servidores/{id}/constructor/aplicar   — (fase 2 con cola; fase 1 devuelve instrucciones)
- POST /servidores/{id}/constructor/deshacer  — (fase 2 con cola)
- GET/PUT /servidores/{id}/modulos/{modulo}   — configuración de cada módulo
- GET/PUT /servidores/{id}/conocimiento       — base de conocimiento
- GET /servidores/{id}/analiticas             — métricas básicas
- POST /facturacion/suscribir   — inicia el pago (PayPal)
- POST /paypal/webhook          — recibe avisos de PayPal (con verificación de firma)
- GET  /estado                  — salud de la API
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ia import Cerebro, RAG
from bot import constructor
from bot.db import BaseDatos
from api.seguridad import Seguridad

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="Plataforma IA para Discord", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restringir al dominio de la PWA en producción
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = BaseDatos(os.environ.get("DATABASE_PATH", "data/plataforma.db"))
RAG_DB = RAG(os.environ.get("DATABASE_PATH", "data/plataforma.db"))
CEREBRO = Cerebro(RAG_DB, os.environ.get("DATABASE_PATH", "data/plataforma.db"))
SEGURIDAD = Seguridad(os.environ.get("DATABASE_PATH", "data/plataforma.db"))

DISCORD_API = "https://discord.com/api/v10"


# ---------------------------------------------------------------- modelos

class CodigoOAuth(BaseModel):
    codigo: str


class PlanEntrada(BaseModel):
    descripcion: str


class ModuloConfig(BaseModel):
    activo: bool = True
    configuracion: dict = {}


class ConocimientoEntrada(BaseModel):
    titulo: str
    contenido: str


class SuscripcionEntrada(BaseModel):
    servidor_id: str
    plan: str  # "pro" | "business"


# ---------------------------------------------------------------- utilidades

_TOKENS_SESION: dict[str, dict] = {}


async def sesion_actual(request: Request) -> dict:
    autorizacion = request.headers.get("Authorization", "")
    token = autorizacion.removeprefix("Bearer ").strip()
    sesion = _TOKENS_SESION.get(token)
    if not sesion:
        raise HTTPException(401, "Sesión inválida o expirada")
    return sesion


@app.on_event("startup")
async def al_arrancar():
    await DB.inicializar()
    await DB.inicializar_negocio()


@app.middleware("http")
async def escudo_seguridad(request: Request, call_next):
    ip = request.client.host if request.client else "desconocida"
    if SEGURIDAD.esta_baneada(ip):
        return JSONResponse({"error": "Acceso bloqueado permanentemente"}, status_code=403)
    if not SEGURIDAD.permitir(ip):
        SEGURIDAD.registrar_evento("rate_limit", ip, "Exceso de peticiones")
        return JSONResponse({"error": "Demasiadas peticiones"}, status_code=429)
    respuesta = await call_next(request)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "no-referrer"
    return respuesta


# ---------------------------------------------------------------- estado

@app.get("/estado")
async def estado():
    return {
        "ok": True,
        "ia_disponible": CEREBRO.disponible,
        "version": app.version,
    }


# ---------------------------------------------------------------- auth

@app.post("/auth/discord")
async def auth_discord(datos: CodigoOAuth, request: Request):
    if not os.environ.get("DISCORD_CLIENT_SECRET"):
        raise HTTPException(503, "OAuth2 de Discord no configurado en el servidor")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{DISCORD_API}/oauth2/token",
            data={
                "client_id": os.environ["DISCORD_CLIENT_ID"],
                "client_secret": os.environ["DISCORD_CLIENT_SECRET"],
                "grant_type": "authorization_code",
                "code": datos.codigo,
                "redirect_uri": os.environ.get("DISCORD_REDIRECT_URI", "http://localhost:8000/auth/discord/callback"),
            },
        )
        if r.status_code != 200:
            ip = request.client.host if request.client else ""
            baneado = SEGURIDAD.registrar_intento_fallido(ip)
            raise HTTPException(400, "Código OAuth2 inválido" + (" · IP baneada permanentemente" if baneado else ""))
        token = r.json()
        r_usuario = await client.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        )
        usuario = r_usuario.json()

    token_sesion = secrets.token_urlsafe(32)
    _TOKENS_SESION[token_sesion] = {"usuario": usuario, "access_token": token["access_token"]}
    return {"token": token_sesion, "usuario": {"id": usuario["id"], "username": usuario["username"]}}


@app.get("/servidores")
async def listar_servidores(sesion: dict = Depends(sesion_actual)):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{DISCORD_API}/users/@me/guilds",
            headers={"Authorization": f"Bearer {sesion['access_token']}"},
        )
    if r.status_code != 200:
        raise HTTPException(502, "No se pudieron obtener los servidores de Discord")
    administrables = [
        {"id": g["id"], "nombre": g["name"], "icono": g.get("icon"), "dueno": g["owner"]}
        for g in r.json()
        if g["owner"] or (int(g.get("permissions", 0)) & 0x20)  # MANAGE_GUILD
    ]
    return {"servidores": administrables}


# ---------------------------------------------------------------- constructor

@app.post("/servidores/{servidor_id}/constructor/plan")
async def plan_constructor(servidor_id: str, datos: PlanEntrada, sesion: dict = Depends(sesion_actual)):
    plan = await CEREBRO.plan_constructor(datos.descripcion)
    try:
        constructor.validar(plan)
    except constructor.PlanInvalido as error:
        raise HTTPException(422, str(error))
    return {"plan": plan, "ia_disponible": CEREBRO.disponible}


@app.post("/servidores/{servidor_id}/constructor/aplicar")
async def aplicar_plan(servidor_id: str, datos: PlanEntrada, sesion: dict = Depends(sesion_actual)):
    """Fase 1: devuelve el plan validado para aplicarlo con /construir-aplicar.
    Fase 2: lo enviará al bot por la cola de tareas."""
    plan = await CEREBRO.plan_constructor(datos.descripcion)
    try:
        constructor.validar(plan)
    except constructor.PlanInvalido as error:
        raise HTTPException(422, str(error))
    return {"estado": "validado", "plan": plan, "instruccion": "Usa /construir-aplicar en el servidor"}


@app.post("/servidores/{servidor_id}/constructor/deshacer")
async def deshacer_plan(servidor_id: str, sesion: dict = Depends(sesion_actual)):
    registro = await DB.registro_pendiente(servidor_id)
    return {"estado": "validado", "objetos_a_revertir": len(registro), "instruccion": "Usa /construir-deshacer en el servidor"}


# ---------------------------------------------------------------- módulos

MODULOS_VALIDOS = {
    "bienvenida", "moderacion", "anti_spam", "verificacion", "logs",
    "roles_botones", "encuestas", "tickets", "pregunta", "constructor",
    "niveles", "sorteos", "sugerencias", "recordatorios", "anuncios",
    "backups", "resumenes", "anti_nuke", "tienda",
}


@app.get("/servidores/{servidor_id}/modulos/{modulo}")
async def obtener_modulo(servidor_id: str, modulo: str, sesion: dict = Depends(sesion_actual)):
    if modulo not in MODULOS_VALIDOS:
        raise HTTPException(404, "Módulo desconocido")
    return {"modulo": modulo, "activo": await DB.modulo_activo(servidor_id, modulo)}


@app.put("/servidores/{servidor_id}/modulos/{modulo}")
async def fijar_modulo(servidor_id: str, modulo: str, datos: ModuloConfig, sesion: dict = Depends(sesion_actual)):
    if modulo not in MODULOS_VALIDOS:
        raise HTTPException(404, "Módulo desconocido")
    await DB.fijar_modulo(servidor_id, modulo, datos.activo)
    return {"modulo": modulo, "activo": datos.activo}


# ---------------------------------------------------------------- conocimiento

@app.get("/servidores/{servidor_id}/conocimiento")
async def listar_conocimiento(servidor_id: str, sesion: dict = Depends(sesion_actual)):
    return {"documentos": [f.__dict__ for f in RAG_DB.listar(servidor_id)]}


@app.put("/servidores/{servidor_id}/conocimiento")
async def añadir_conocimiento(servidor_id: str, datos: ConocimientoEntrada, sesion: dict = Depends(sesion_actual)):
    id_ = RAG_DB.añadir(servidor_id, datos.titulo, datos.contenido)
    return {"id": id_}


@app.delete("/servidores/{servidor_id}/conocimiento/{documento_id}")
async def eliminar_conocimiento(servidor_id: str, documento_id: str, sesion: dict = Depends(sesion_actual)):
    if not RAG_DB.eliminar(servidor_id, documento_id):
        raise HTTPException(404, "Documento no encontrado")
    return {"ok": True}


# ---------------------------------------------------------------- analíticas

@app.get("/servidores/{servidor_id}/analiticas")
async def analiticas(servidor_id: str, sesion: dict = Depends(sesion_actual)):
    activos = 0
    for m in MODULOS_VALIDOS:
        if await DB.modulo_activo(servidor_id, m):
            activos += 1
    return {
        "servidor_id": servidor_id,
        "modulos_activos": activos,
        "documentos_conocimiento": len(RAG_DB.listar(servidor_id)),
        "fase": "1 (analíticas completas en fase 2)",
    }


# ---------------------------------------------------------------- seguridad (panel)

@app.get("/seguridad/eventos")
async def eventos_seguridad(sesion: dict = Depends(sesion_actual)):
    return {"eventos": SEGURIDAD.eventos(), "bans": SEGURIDAD.bans()}


@app.delete("/seguridad/bans/{ip}")
async def desbanear_ip(ip: str, sesion: dict = Depends(sesion_actual)):
    if not SEGURIDAD.desbanear(ip):
        raise HTTPException(404, "Ban no encontrado")
    return {"ok": True}


# ---------------------------------------------------------------- negocio (panel del dueño)

DATOS_EJEMPLO_NEGOCIO = [
    {"servidor_id": "demo", "plan": "pro", "monto": 8.0, "tipo": "pago", "origen": "ejemplo"},
    {"servidor_id": "demo", "plan": "pro", "monto": 8.0, "tipo": "pago", "origen": "ejemplo"},
    {"servidor_id": "demo", "plan": "business", "monto": 30.0, "tipo": "pago", "origen": "ejemplo"},
    {"servidor_id": "demo", "plan": "pro", "monto": 8.0, "tipo": "reembolso", "origen": "ejemplo"},
]


@app.get("/negocio/resumen")
async def negocio_resumen(sesion: dict = Depends(sesion_actual), servidor_id: str | None = None):
    resumen = await DB.resumen_negocio(servidor_id)
    if not resumen["transacciones"] and not os.environ.get("PAYPAL_CLIENT_ID"):
        for pago in DATOS_EJEMPLO_NEGOCIO:
            await DB.registrar_pago(pago["servidor_id"], pago["plan"], pago["monto"], pago["tipo"], pago["origen"])
        resumen = await DB.resumen_negocio(servidor_id)
        resumen["modo"] = "ejemplo"
    else:
        resumen["modo"] = "real"
    return resumen


@app.get("/servidores/{servidor_id}/tienda")
async def listar_tienda(servidor_id: str, sesion: dict = Depends(sesion_actual)):
    productos = await DB.productos_de(servidor_id)
    ventas = await DB.ventas_tienda_de(servidor_id)
    return {"productos": productos, "ventas": ventas, "cobrado": sum(v["monto"] for v in ventas if v["estado"] == "pagada")}


@app.post("/servidores/{servidor_id}/tienda")
async def añadir_producto_tienda(servidor_id: str, datos: dict, sesion: dict = Depends(sesion_actual)):
    nombre = str(datos.get("nombre", "")).strip()[:100]
    precio = round(float(datos.get("precio", 0)), 2)
    if not nombre or precio < 0.5:
        raise HTTPException(400, "Nombre y precio (mínimo 0.5) obligatorios")
    id_ = await DB.añadir_producto(servidor_id, nombre, str(datos.get("descripcion", ""))[:500], precio, str(datos.get("entrega", ""))[:300])
    return {"id": id_}


@app.post("/negocio/pago")
async def negocio_registrar_pago(servidor_id: str, plan: str, monto: float, tipo: str = "pago", sesion: dict = Depends(sesion_actual)):
    if tipo not in {"pago", "reembolso"}:
        raise HTTPException(400, "Tipo debe ser pago o reembolso")
    id_ = await DB.registrar_pago(servidor_id, plan, monto, tipo, origen="manual")
    return {"id": id_}


# ---------------------------------------------------------------- PayPal

PLANES = {
    "pro": {"nombre": "Pro", "precio_mensual_usd": 8.0},
    "business": {"nombre": "Business", "precio_mensual_usd": 30.0},
}


@app.post("/facturacion/suscribir")
async def suscribir(datos: SuscripcionEntrada, sesion: dict = Depends(sesion_actual)):
    if datos.plan not in PLANES:
        raise HTTPException(400, "Plan desconocido")
    client_id = os.environ.get("PAYPAL_CLIENT_ID")
    if not client_id:
        raise HTTPException(503, "PayPal no configurado. Usa el cobro manual (paypal.me) en la fase 1.")
    base = os.environ.get("PAYPAL_BASE", "https://api-m.sandbox.paypal.com")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{base}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, os.environ["PAYPAL_SECRET"]),
        )
        r.raise_for_status()
        access = r.json()["access_token"]
        return {"estado": "configurado", "plan": datos.plan, "siguiente": "crear suscripción con plan_id de PayPal"}
    # Nota: la creación real de la suscripción (POST /v1/billing/subscriptions
    # con plan_id y custom_id=servidor_id) se completa con los plan_id reales.


@app.post("/paypal/webhook")
async def paypal_webhook(request: Request):
    """Verifica la firma del webhook antes de actuar (sección 10.4 de la guía)."""
    evento = await request.json()
    h = request.headers
    webhook_id = os.environ.get("PAYPAL_WEBHOOK_ID")
    if not webhook_id or not os.environ.get("PAYPAL_CLIENT_ID"):
        raise HTTPException(503, "PayPal no configurado")
    base = os.environ.get("PAYPAL_BASE", "https://api-m.sandbox.paypal.com")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{base}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(os.environ["PAYPAL_CLIENT_ID"], os.environ["PAYPAL_SECRET"]),
        )
        r.raise_for_status()
        access = r.json()["access_token"]
        v = await client.post(
            f"{base}/v1/notifications/verify-webhook-signature",
            headers={"Authorization": f"Bearer {access}"},
            json={
                "auth_algo": h.get("paypal-auth-algo"),
                "cert_url": h.get("paypal-cert-url"),
                "transmission_id": h.get("paypal-transmission-id"),
                "transmission_sig": h.get("paypal-transmission-sig"),
                "transmission_time": h.get("paypal-transmission-time"),
                "webhook_id": webhook_id,
                "webhook_event": evento,
            },
        )
    if v.json().get("verification_status") != "SUCCESS":
        raise HTTPException(400, "Firma inválida")

    tipo = evento.get("event_type", "")
    recurso = evento.get("resource") or {}
    guild_id = recurso.get("custom_id")
    if tipo == "BILLING.SUBSCRIPTION.ACTIVATED" and guild_id:
        await DB.fijar_modulo(guild_id, "constructor", True)
    elif tipo == "PAYMENT.SALE.COMPLETED" and guild_id:
        monto = float((recurso.get("amount") or {}).get("total", 0) or 0)
        await DB.registrar_pago(guild_id, "pro", monto, "pago", origen="paypal")
    elif tipo in {"BILLING.SUBSCRIPTION.CANCELLED", "BILLING.SUBSCRIPTION.SUSPENDED", "BILLING.SUBSCRIPTION.EXPIRED"} and guild_id:
        await DB.fijar_modulo(guild_id, "constructor", False)
    return {"ok": True}

