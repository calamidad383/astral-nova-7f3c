"""Módulo de moderación base: advertir, silenciar, expulsar, banear, historial.

La IA solo sugiere (ver cog pregunta / cerebro); un humano decide aquí.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class Moderacion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    grupo = app_commands.Group(name="mod", description="Moderación del servidor")

    async def _registrar(self, interaction: discord.Interaction, tipo: str, usuario: discord.Member, motivo: str):
        await self.bot.db.registrar_caso(
            str(interaction.guild_id), str(usuario.id), str(interaction.user.id), tipo, motivo
        )

    @grupo.command(name="advertir")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def advertir(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str):
        await self._registrar(interaction, "advertencia", usuario, motivo)
        await interaction.response.send_message(
            f"⚠️ {usuario.mention} advertido. Motivo: {motivo}", ephemeral=False
        )

    @grupo.command(name="silenciar")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def silenciar(self, interaction: discord.Interaction, usuario: discord.Member, minutos: int, motivo: str):
        await usuario.timeout(discord.utils.utcnow() + discord.timedelta(minutes=minutos), reason=motivo)
        await self._registrar(interaction, "silencio", usuario, motivo)
        await interaction.response.send_message(
            f"🔇 {usuario.mention} silenciado {minutos} min. Motivo: {motivo}"
        )

    @grupo.command(name="expulsar")
    @app_commands.checks.has_permissions(kick_members=True)
    async def expulsar(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str):
        await usuario.kick(reason=motivo)
        await self._registrar(interaction, "expulsion", usuario, motivo)
        await interaction.response.send_message(f"👢 {usuario.name} expulsado. Motivo: {motivo}")

    @grupo.command(name="banear")
    @app_commands.checks.has_permissions(ban_members=True)
    async def banear(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str):
        await usuario.ban(reason=motivo)
        await self._registrar(interaction, "baneo", usuario, motivo)
        await interaction.response.send_message(f"🔨 {usuario.name} baneado. Motivo: {motivo}")

    @grupo.command(name="historial")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def historial(self, interaction: discord.Interaction, usuario: discord.Member):
        casos = await self.bot.db.casos_de(str(interaction.guild_id), str(usuario.id))
        if not casos:
            await interaction.response.send_message(f"{usuario.name} no tiene casos registrados.", ephemeral=True)
            return
        lineas = [f"• [{c['creado_en']}] {c['tipo']}: {c['motivo'] or '(sin motivo)'}" for c in casos[:10]]
        await interaction.response.send_message(
            f"Historial de {usuario.name} ({len(casos)} casos):\n" + "\n".join(lineas), ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Moderacion(bot))
