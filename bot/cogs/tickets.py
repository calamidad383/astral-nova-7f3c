"""Módulo de tickets: canales privados de soporte con cierre y registro."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class VistaTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="abrir_ticket")
    async def abrir(self, interaction: discord.Interaction, boton: discord.ui.Button):
        guild = interaction.guild
        existente = discord.utils.get(
            guild.text_channels, name=f"ticket-{interaction.user.name.lower()}"
        )
        if existente:
            await interaction.response.send_message(f"Ya tienes un ticket: {existente.mention}", ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        for rol in guild.roles:
            if rol.permissions.manage_guild:
                overwrites[rol] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        canal = await guild.create_text_channel(
            f"ticket-{interaction.user.name.lower()}", overwrites=overwrites, reason="Ticket de soporte"
        )
        await self.bot.db.crear_ticket(str(guild.id), str(canal.id), str(interaction.user.id))
        await canal.send(
            f"🎫 Ticket de {interaction.user.mention}. Describe tu problema; el staff atenderá pronto.",
            view=VistaCierre(),
        )
        await interaction.response.send_message(f"Ticket creado: {canal.mention}", ephemeral=True)


class VistaCierre(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cerrar ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="cerrar_ticket")
    async def cerrar(self, interaction: discord.Interaction, boton: discord.ui.Button):
        await self.bot.db.cerrar_ticket(str(interaction.guild_id), str(interaction.channel_id))
        await interaction.response.send_message("Cerrando el ticket en 5 segundos…")
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=5))
        await interaction.channel.delete(reason="Ticket cerrado")


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(VistaTicket())
        bot.add_view(VistaCierre())

    @app_commands.command(name="panel-tickets", description="Publica el panel de tickets en el canal actual")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def panel_tickets(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🎫 ¿Necesitas ayuda? Abre un ticket privado con el staff.", view=VistaTicket()
        )


async def setup(bot):
    await bot.add_cog(Tickets(bot))
