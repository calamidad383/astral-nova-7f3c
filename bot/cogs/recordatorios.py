"""Módulo de recordatorios personales y del servidor."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("bot.recordatorios")

MULTIPLICADORES = {"m": 1, "min": 1, "minutos": 1, "h": 60, "horas": 60, "d": 1440, "dias": 1440, "días": 1440}


def _parsear_minutos(texto: str) -> int | None:
    coincidencia = re.fullmatch(r"(\d+)\s*(m|min|minutos|h|horas|d|dias|días)", texto.strip().lower())
    if not coincidencia:
        return None
    return int(coincidencia.group(1)) * MULTIPLICADORES[coincidencia.group(2)]


class Recordatorios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tarea = bot.loop.create_task(self.bucle()) if bot.loop else None

    async def bucle(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
                for rec in await self.bot.db.recordatorios_pendientes(ahora):
                    canal = self.bot.get_channel(int(rec["canal_id"]))
                    if canal:
                        await canal.send(f"⏰ <@{rec['usuario_id']}> Recordatorio: {rec['texto']}")
                    await self.bot.db.marcar_recordatorio(rec["id"])
            except Exception:
                log.exception("Error en el bucle de recordatorios")
            await asyncio.sleep(20)

    @app_commands.command(name="recordar", description="Crea un recordatorio. Ej.: 30m, 2h, 1d")
    async def recordar(self, interaction: discord.Interaction, cuando: str, texto: str):
        minutos = _parsear_minutos(cuando)
        if minutos is None or minutos < 1 or minutos > 43200:
            await interaction.response.send_message("Duración inválida. Ejemplos: 30m, 2h, 1d.", ephemeral=True)
            return
        cuando_iso = (datetime.now(timezone.utc) + timedelta(minutes=minutos)).isoformat(timespec="seconds")
        await self.bot.db.crear_recordatorio(
            str(interaction.guild_id), str(interaction.channel_id), str(interaction.user.id), texto, cuando_iso
        )
        await interaction.response.send_message(f"⏰ De acuerdo. Te recuerdo en {cuando}: {texto[:100]}")


async def setup(bot):
    await bot.add_cog(Recordatorios(bot))
