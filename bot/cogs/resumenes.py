"""Módulo de resúmenes de canales con el motor de IA local."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class Resumenes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="resumen", description="Resume la actividad reciente de un canal")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def resumen(self, interaction: discord.Interaction, cantidad: int = 100):
        await interaction.response.defer(thinking=True)
        cantidad = max(10, min(cantidad, 300))
        mensajes = []
        async for mensaje in interaction.channel.history(limit=cantidad):
            if mensaje.author.bot or not mensaje.content:
                continue
            autor = mensaje.author.name[:3] + "***"
            mensajes.append(f"{autor}: {mensaje.content}")
        if not mensajes:
            await interaction.followup.send("No hay mensajes suficientes para resumir.")
            return
        texto = await self.bot.cerebro.resumir(str(interaction.guild_id), interaction.guild.name, mensajes)
        embed = discord.Embed(title=f"📋 Resumen de #{interaction.channel.name}", description=texto[:3900], color=discord.Color.blurple())
        embed.set_footer(text=f"Últimos {len(mensajes)} mensajes · IA local")
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Resumenes(bot))
