"""Módulo de sorteos con selección de ganador verificable."""

from __future__ import annotations

import random

import discord
from discord import app_commands
from discord.ext import commands


class VistaSorteo(discord.ui.View):
    def __init__(self, premio: str):
        super().__init__(timeout=None)
        self.premio = premio
        self.participantes: set[int] = set()

    @discord.ui.button(label="Participar", style=discord.ButtonStyle.success, emoji="🎉", custom_id="participar")
    async def participar(self, interaction: discord.Interaction, boton: discord.ui.Button):
        self.participantes.add(interaction.user.id)
        await interaction.response.send_message(f"¡Apuntado! ({len(self.participantes)} participantes)", ephemeral=True)


class Sorteos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sorteo", description="Inicia un sorteo con selección verificable de ganador")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def sorteo(self, interaction: discord.Interaction, premio: str, minutos: int):
        duracion = max(1, min(minutos, 10080))
        vista = VistaSorteo(premio)
        mensaje = await interaction.channel.send(
            f"🎁 **SORTEO: {premio}**\nTermina en {duracion} min. ¡Pulsa para participar!",
            view=vista,
        )
        await asyncio_sleep(duracion * 60)
        participantes = list(vista.participantes)
        if not participantes:
            await interaction.channel.send("El sorteo terminó sin participantes.")
            return
        semilla = mensaje.id
        ganador_id = random.Random(semilla).choice(participantes)
        await interaction.channel.send(
            f"🏆 **Ganador del sorteo de {premio}:** <@{ganador_id}>\n"
            f"Selección verificable: semilla {semilla} sobre {len(participantes)} participantes."
        )


async def asyncio_sleep(segundos: float):
    import asyncio

    await asyncio.sleep(segundos)


async def setup(bot):
    await bot.add_cog(Sorteos(bot))
