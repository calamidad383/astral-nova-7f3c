"""Módulo `/pregunta`: respuestas de la IA con citas de la base de conocimiento."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class Pregunta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pregunta", description="Pregunta a la IA del servidor (responde con fuentes)")
    async def pregunta(self, interaction: discord.Interaction, texto: str):
        if not await self.bot.db.modulo_activo(str(interaction.guild_id), "pregunta"):
            await interaction.response.send_message("El módulo de IA está desactivado en este servidor.", ephemeral=True)
            return
        await interaction.response.defer(thinking=True)
        try:
            respuesta = await self.bot.cerebro.responder_pregunta(
                str(interaction.guild_id), interaction.guild.name, texto
            )
        except Exception:
            await interaction.followup.send(
                "La IA no está disponible ahora mismo. Derivaré tu pregunta a un moderador."
            )
            return
        fuentes = f"\n\nFuentes: {', '.join(respuesta.fuentes)}" if respuesta.fuentes else ""
        embed = discord.Embed(description=respuesta.texto[:3900] + fuentes, color=discord.Color.blurple())
        embed.set_footer(text=f"Respondido por IA · modo: {respuesta.modo}")
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Pregunta(bot))
