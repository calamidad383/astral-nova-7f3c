"""Módulo anti-spam: mensajes repetidos, menciones excesivas y enlaces masivos."""

from __future__ import annotations

import time
from collections import defaultdict, deque

import discord
from discord.ext import commands

VENTANA = 10.0
MAX_MENSAJES = 6
MAX_MENCIONES = 8
MAX_ENLACES = 4


class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.historial: dict[tuple[int, int], deque] = defaultdict(lambda: deque(maxlen=20))

    @commands.Cog.listener()
    async def on_message(self, mensaje: discord.Message):
        if mensaje.author.bot or not mensaje.guild:
            return
        if not await self.bot.db.modulo_activo(str(mensaje.guild.id), "anti_spam"):
            return
        if mensaje.author.guild_permissions.manage_messages:
            return

        clave = (mensaje.guild.id, mensaje.author.id)
        ahora = time.monotonic()
        historial = self.historial[clave]
        historial.append((ahora, mensaje.content))

        recientes = [c for t, c in historial if ahora - t <= VENTANA]
        razon = None
        if len(recientes) >= MAX_MENSAJES and len(set(recientes)) <= 2:
            razon = "mensajes repetidos"
        elif sum(m.count("<@") for m in recientes) >= MAX_MENCIONES:
            razon = "menciones excesivas"
        elif sum(m.count("http") for m in recientes) >= MAX_ENLACES:
            razon = "enlaces masivos"

        if razon:
            try:
                await mensaje.author.timeout(
                    discord.utils.utcnow() + discord.timedelta(minutes=10),
                    reason=f"Anti-spam: {razon}",
                )
                await self.bot.db.registrar_caso(
                    str(mensaje.guild.id), str(mensaje.author.id), str(self.bot.user.id),
                    "silencio", f"Anti-spam automático: {razon}",
                )
                await mensaje.channel.send(
                    f"🛑 {mensaje.author.mention} silenciado 10 min por {razon}.",
                    delete_after=10,
                )
                historial.clear()
            except discord.Forbidden:
                pass


async def setup(bot):
    await bot.add_cog(AntiSpam(bot))
