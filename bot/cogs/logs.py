"""Módulo de registros (logs): entradas, salidas, mensajes borrados y editados."""

from __future__ import annotations

import discord
from discord.ext import commands


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _canal_logs(self, guild: discord.Guild) -> discord.TextChannel | None:
        return discord.utils.get(guild.text_channels, name="registro")

    @commands.Cog.listener()
    async def on_message_delete(self, mensaje: discord.Message):
        if not mensaje.guild or mensaje.author.bot:
            return
        if not await self.bot.db.modulo_activo(str(mensaje.guild.id), "logs"):
            return
        canal = self._canal_logs(mensaje.guild)
        if canal:
            contenido = mensaje.content[:500] or "(sin texto)"
            await canal.send(f"🗑️ Mensaje de {mensaje.author.name} borrado en {mensaje.channel.mention}: {contenido}")

    @commands.Cog.listener()
    async def on_message_edit(self, antes: discord.Message, despues: discord.Message):
        if not antes.guild or antes.author.bot or antes.content == despues.content:
            return
        if not await self.bot.db.modulo_activo(str(antes.guild.id), "logs"):
            return
        canal = self._canal_logs(antes.guild)
        if canal:
            await canal.send(
                f"✏️ {antes.author.name} editó en {antes.channel.mention}:\n"
                f"Antes: {antes.content[:300] or '(vacío)'}\nDespués: {despues.content[:300]}"
            )

    @commands.Cog.listener()
    async def on_member_join(self, miembro: discord.Member):
        if not await self.bot.db.modulo_activo(str(miembro.guild.id), "logs"):
            return
        canal = self._canal_logs(miembro.guild)
        if canal:
            await canal.send(f"📥 {miembro.name} entró (cuenta creada: {miembro.created_at:%Y-%m-%d})")

    @commands.Cog.listener()
    async def on_member_remove(self, miembro: discord.Member):
        if not await self.bot.db.modulo_activo(str(miembro.guild.id), "logs"):
            return
        canal = self._canal_logs(miembro.guild)
        if canal:
            await canal.send(f"📤 {miembro.name} salió")


async def setup(bot):
    await bot.add_cog(Logs(bot))
