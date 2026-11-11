"""Constructor de servidores con IA: validar, aplicar y deshacer (sección 6 de la guía).

Reglas de seguridad:
- Nunca se asigna Administrador; los permisos salen de plantillas fijas.
- Topes estrictos (30 roles, 100 canales) muy por debajo de los límites de Discord.
- Pausas entre acciones para respetar la API.
- Todo queda registrado para poder deshacer en orden inverso.
"""

from __future__ import annotations

import asyncio

import discord

MAX_ROLES = 30
MAX_CANALES = 100
PAUSA = 1.0

PLANTILLAS = {
    "miembro": discord.Permissions(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        connect=True,
        speak=True,
    ),
    "moderador": discord.Permissions(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        manage_messages=True,
        kick_members=True,
        moderate_members=True,
    ),
}


class PlanInvalido(ValueError):
    pass


def validar(plan: dict) -> None:
    if not isinstance(plan, dict):
        raise PlanInvalido("El plan debe ser un objeto JSON")
    roles = plan.get("roles", [])
    categorias = plan.get("categorias", [])
    if len(roles) > MAX_ROLES:
        raise PlanInvalido(f"Demasiados roles ({len(roles)} > {MAX_ROLES})")
    total = sum(len(c.get("canales", [])) + 1 for c in categorias)
    if total > MAX_CANALES:
        raise PlanInvalido(f"Demasiados canales ({total} > {MAX_CANALES})")
    for r in roles:
        if r.get("plantilla") not in PLANTILLAS:
            raise PlanInvalido(f"Plantilla desconocida: {r.get('plantilla')}")
    for c in categorias:
        for canal in c.get("canales", []):
            if canal.get("tipo") not in {"texto", "voz"}:
                raise PlanInvalido(f"Tipo de canal desconocido: {canal.get('tipo')}")


def normalizar_nombre(nombre: str) -> str:
    nombre = nombre.strip().lower()
    tabla = str.maketrans("áéíóúüñ ", "aeiouun-")
    nombre = nombre.translate(tabla)
    return "-".join(p for p in nombre.split("-") if p)[:90] or "canal"


async def aplicar(guild: discord.Guild, plan: dict, registrar) -> dict:
    """Aplica el plan. `registrar(tipo, objeto_id)` guarda cada acción.

    Devuelve un diccionario con los objetos creados (para mensajes posteriores).
    """
    validar(plan)
    creados: dict = {"roles": {}, "canales": {}}

    for r in plan.get("roles", []):
        rol = await guild.create_role(
            name=r["nombre"],
            colour=discord.Colour.from_str(r["color"]),
            permissions=PLANTILLAS[r["plantilla"]],
            reason="Constructor IA",
        )
        creados["roles"][r["nombre"]] = rol
        registrar("rol", str(rol.id))
        await asyncio.sleep(PAUSA)

    for cat in plan.get("categorias", []):
        categoria = await guild.create_category(cat["nombre"], reason="Constructor IA")
        registrar("categoria", str(categoria.id))
        await asyncio.sleep(PAUSA)
        for c in cat.get("canales", []):
            overwrites = {}
            if c.get("solo_lectura"):
                overwrites[guild.default_role] = discord.PermissionOverwrite(send_messages=False)
            nombre = normalizar_nombre(c["nombre"])
            if c["tipo"] == "voz":
                canal = await guild.create_voice_channel(nombre, category=categoria, overwrites=overwrites, reason="Constructor IA")
            else:
                canal = await guild.create_text_channel(nombre, category=categoria, overwrites=overwrites, reason="Constructor IA")
            creados["canales"][nombre] = canal
            registrar("canal", str(canal.id))
            await asyncio.sleep(PAUSA)

    for m in plan.get("mensajes", []):
        canal = creados["canales"].get(normalizar_nombre(m["canal"]))
        if canal and isinstance(canal, discord.TextChannel):
            await canal.send(m["contenido"][:1900])

    return creados


async def deshacer(guild: discord.Guild, registro: list[tuple[str, str]]) -> int:
    """Elimina en orden inverso lo creado. Devuelve cuántos objetos eliminó."""
    eliminados = 0
    for tipo, id_ in registro:
        objeto = guild.get_role(int(id_)) if tipo == "rol" else guild.get_channel(int(id_))
        if objeto:
            await objeto.delete(reason="Deshacer constructor IA")
            eliminados += 1
            await asyncio.sleep(PAUSA)
    return eliminados
