"""Módulo anti-nuke: detecta destrucción masiva del servidor y entra en cuarentena.

- Vigila el audit log: baneos, expulsiones, canales borrados y roles borrados.
- Si un actor supera el umbral en la ventana de tiempo, se le quitan todos los
  roles (cuarentena), se avisa al canal del sistema y queda registrado.
- La restauración se hace con /backup-restaurar (módulo de copias).
"""

from __future__ import annotations

import time
from collections import defaultdict

import discord
from discord.ext import commands

VENTANA = 60.0
UMBRALES = {"ban": 5, "kick": 5, "canal_borrado": 3, "rol_borrado": 3}


class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.acciones: dict[tuple[int, int, str], list[float]] = defaultdict(list)

    async def _registrar_accion(self, guild: discord.Guild, actor_id: int, tipo: str) -> bool:
        clave = (guild.id, actor_id, tipo)
        ahora = time.monotonic()
        lista = self.acciones[clave]
        lista.append(ahora)
        while lista and ahora - lista[0] > VENTANA:
            lista.popleft()
        return len(lista) >= UMBRALES.get(tipo, 4)

    async def _cuarentena(self, guild: discord.Guild, actor_id: int, tipo: str):
        miembro = guild.get_member(actor_id)
        canal = guild.system_channel
        aviso = (
            f"🚨 **MODO CUARENTENA**: <@{actor_id}> eliminó múltiples objetos ({tipo}). "
            "Se le retiraron los roles y se alertó al staff."
        )
        if miembro:
            roles_peligrosos = [r for r in miembro.roles if r != guild.default_role and r < guild.me.top_role]
            try:
                await miembro.remove_roles(*roles_peligrosos, reason=f"Anti-nuke: {tipo} masivo")
            except discord.Forbidden:
                aviso += "\n⚠️ No pude retirar los roles (permisos insuficientes)."
        if canal:
            await canal.send(aviso)
        await self.bot.db.registrar_caso(
            str(guild.id), str(actor_id), str(self.bot.user.id), "cuarentena", f"Anti-nuke: {tipo} masivo"
        )

    async def _actor_reciente(self, guild: discord.Guild, accion, excluir_bots: bool = True) -> int | None:
        async for entrada in guild.audit_logs(limit=5, action=accion):
            if (discord.utils.utcnow() - entrada.created_at).total_seconds() > 10:
                break
            if entrada.user and entrada.user.bot:
                continue
            return entrada.user.id
        return None

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, canal):
        guild = canal.guild
        if not await self.bot.db.modulo_activo(str(guild.id), "anti_nuke"):
            return
        actor = await self._actor_reciente(guild, discord.AuditLogAction.channel_delete)
        if actor and await self._registrar_accion(guild, actor, "canal_borrado"):
            await self._cuarentena(guild, actor, "borrado de canales")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, rol):
        guild = rol.guild
        if not await self.bot.db.modulo_activo(str(guild.id), "anti_nuke"):
            return
        actor = await self._actor_reciente(guild, discord.AuditLogAction.role_delete)
        if actor and await self._registrar_accion(guild, actor, "rol_borrado"):
            await self._cuarentena(guild, actor, "borrado de roles")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, usuario):
        if not await self.bot.db.modulo_activo(str(guild.id), "anti_nuke"):
            return
        actor = await self._actor_reciente(guild, discord.AuditLogAction.ban)
        if actor and await self._registrar_accion(guild, actor, "ban"):
            await self._cuarentena(guild, actor, "baneos masivos")

    @commands.Cog.listener()
    async def on_member_remove(self, miembro):
        guild = miembro.guild
        if not await self.bot.db.modulo_activo(str(guild.id), "anti_nuke"):
            return
        actor = await self._actor_reciente(guild, discord.AuditLogAction.kick)
        if actor and await self._registrar_accion(guild, actor, "kick"):
            await self._cuarentena(guild, actor, "expulsiones masivas")


async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
