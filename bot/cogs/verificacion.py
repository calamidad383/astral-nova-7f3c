"""Módulo de verificación: los nuevos miembros se verifican con un botón."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class VistaVerificacion(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verificarme", style=discord.ButtonStyle.success, emoji="✅", custom_id="verificar")
    async def verificar(self, interaction: discord.Interaction, boton: discord.ui.Button):
        rol = discord.utils.get(interaction.guild.roles, name="Verificado")
        if rol is None:
            rol = await interaction.guild.create_role(
                name="Verificado",
                permissions=discord.Permissions(view_channel=True, send_messages=True, read_message_history=True),
                reason="Sistema de verificación",
            )
        await interaction.user.add_roles(rol, reason="Verificación con botón")
        await interaction.response.send_message("✅ ¡Verificado! Ya puedes participar.", ephemeral=True)


class Verificacion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(VistaVerificacion())

    @app_commands.command(name="panel-verificacion", description="Publica el panel de verificación")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def panel_verificacion(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🔒 Pulsa el botón para verificar que no eres un bot y acceder al servidor.",
            view=VistaVerificacion(),
        )


async def setup(bot):
    await bot.add_cog(Verificacion(bot))
