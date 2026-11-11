"""Módulo de encuestas con botones y resultados en vivo (API de polls de Discord)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class Encuestas(commands.Cog):
    @app_commands.command(name="encuesta", description="Crea una encuesta con resultados en vivo")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def encuesta(
        self,
        interaction: discord.Interaction,
        pregunta: str,
        opcion1: str,
        opcion2: str,
        opcion3: str | None = None,
        opcion4: str | None = None,
        horas: int = 24,
    ):
        opciones = [o for o in (opcion1, opcion2, opcion3, opcion4) if o]
        if len(opciones) > 10:
            await interaction.response.send_message("Máximo 10 opciones.", ephemeral=True)
            return
        duracion = max(1, min(horas, 168))
        poll = discord.Poll(question=pregunta, duration=duracion * 3600)
        for opcion in opciones:
            poll.add_answer(text=opcion[:55])
        await interaction.response.send_message(poll=poll)


async def setup(bot):
    await bot.add_cog(Encuestas(bot))
