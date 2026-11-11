"""Módulo de sugerencias con votos."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class VotoSugerencia(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.a_favor: set[int] = set()
        self.en_contra: set[int] = set()

    @discord.ui.button(emoji="👍", style=discord.ButtonStyle.success, custom_id="sug_si")
    async def a_favor_boton(self, interaction: discord.Interaction, boton: discord.ui.Button):
        self.a_favor.add(interaction.user.id)
        self.en_contra.discard(interaction.user.id)
        await interaction.response.edit_message(
            content=interaction.message.content.split("\n\n")[0]
            + f"\n\n👍 {len(self.a_favor)}  ·  👎 {len(self.en_contra)}"
        )

    @discord.ui.button(emoji="👎", style=discord.ButtonStyle.danger, custom_id="sug_no")
    async def en_contra_boton(self, interaction: discord.Interaction, boton: discord.ui.Button):
        self.en_contra.add(interaction.user.id)
        self.a_favor.discard(interaction.user.id)
        await interaction.response.edit_message(
            content=interaction.message.content.split("\n\n")[0]
            + f"\n\n👍 {len(self.a_favor)}  ·  👎 {len(self.en_contra)}"
        )


class Sugerencias(commands.Cog):
    @app_commands.command(name="sugerir", description="Envía una sugerencia al servidor")
    async def sugerir(self, interaction: discord.Interaction, sugerencia: str):
        canal = discord.utils.get(interaction.guild.text_channels, name="sugerencias")
        if canal is None:
            canal = await interaction.guild.create_text_channel("sugerencias", reason="Módulo de sugerencias")
        await canal.send(
            f"💡 **Sugerencia de {interaction.user.name}:**\n{sugerencia[:500]}\n\n👍 0  ·  👎 0",
            view=VotoSugerencia(),
        )
        await interaction.response.send_message(f"Sugerencia publicada en {canal.mention}.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Sugerencias(bot))
