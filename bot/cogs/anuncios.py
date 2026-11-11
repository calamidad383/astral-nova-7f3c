"""Módulo de anuncios programados."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("bot.anuncios")


class Anuncios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tarea = bot.loop.create_task(self.bucle()) if bot.loop else None

    async def bucle(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
                for anuncio in await self.bot.db.anuncios_pendientes(ahora):
                    canal = self.bot.get_channel(int(anuncio["canal_id"]))
                    if canal:
                        await canal.send(f"📢 {anuncio['texto']}")
                    await self.bot.db.marcar_anuncio(anuncio["id"])
            except Exception:
                log.exception("Error en el bucle de anuncios")
            await asyncio.sleep(20)

    @app_commands.command(name="anuncio", description="Programa un anuncio (formato fecha: 2026-12-31T18:00)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def anuncio(self, interaction: discord.Interaction, fecha_hora: str, texto: str):
        try:
            cuando = datetime.fromisoformat(fecha_hora).replace(tzinfo=timezone.utc)
        except ValueError:
            await interaction.response.send_message("Fecha inválida. Usa formato 2026-12-31T18:00 (hora UTC).", ephemeral=True)
            return
        await self.bot.db.programar_anuncio(
            str(interaction.guild_id), str(interaction.channel_id), texto, cuando.isoformat(timespec="seconds")
        )
        await interaction.response.send_message(f"📢 Anuncio programado para {fecha_hora} UTC.")


async def setup(bot):
    await bot.add_cog(Anuncios(bot))
