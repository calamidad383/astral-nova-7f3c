"""Módulo de roles por botones (roles por reacción modernizados)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class VistaRoles(discord.ui.View):
    def __init__(self, entradas: list[tuple[str, str]]):
        super().__init__(timeout=None)
        for etiqueta, rol_id in entradas:
            self.add_item(BotonRol(etiqueta, rol_id))


class BotonRol(discord.ui.Button):
    def __init__(self, etiqueta: str, rol_id: str):
        super().__init__(label=etiqueta, style=discord.ButtonStyle.secondary, custom_id=f"rol:{rol_id}")

    async def callback(self, interaction: discord.Interaction):
        rol = interaction.guild.get_role(int(self.custom_id.split(":", 1)[1]))
        if rol is None:
            await interaction.response.send_message("Ese rol ya no existe.", ephemeral=True)
            return
        if rol in interaction.user.roles:
            await interaction.user.remove_roles(rol, reason="Panel de roles")
            await interaction.response.send_message(f"Quitado el rol {rol.name}.", ephemeral=True)
        else:
            await interaction.user.add_roles(rol, reason="Panel de roles")
            await interaction.response.send_message(f"¡Tienes el rol {rol.name}!", ephemeral=True)


class RolesBotones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="panel-roles", description="Publica un panel de roles por botones")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def panel_roles(self, interaction: discord.Interaction, titulo: str, roles: str):
        """Formato de `roles`: Etiqueta:ID separado por comas. Ej: Gamer:123, Artista:456"""
        entradas = []
        for parte in roles.split(","):
            if ":" not in parte:
                continue
            etiqueta, rol_id = parte.split(":", 1)
            if interaction.guild.get_role(int(rol_id.strip())) is None:
                await interaction.response.send_message(f"Rol no encontrado: {rol_id}", ephemeral=True)
                return
            entradas.append((etiqueta.strip(), rol_id.strip()))
        if not entradas:
            await interaction.response.send_message("No se reconoció ningún rol. Usa Etiqueta:ID.", ephemeral=True)
            return
        await interaction.response.send_message(f"**{titulo}** — pulsa para tomar o quitar un rol:", view=VistaRoles(entradas))


async def setup(bot):
    await bot.add_cog(RolesBotones(bot))
