"""Comandos del constructor de servidores con IA (proponer, aplicar, deshacer)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot import constructor


class ConstructorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="construir", description="La IA propone un plan para tu servidor")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def construir(self, interaction: discord.Interaction, descripcion: str):
        await interaction.response.defer(thinking=True)
        plan = await self.bot.cerebro.plan_constructor(descripcion)
        try:
            constructor.validar(plan)
        except constructor.PlanInvalido as error:
            await interaction.followup.send(f"❌ El plan propuesto no es válido: {error}")
            return
        resumen = [f"**Plan propuesto para {interaction.guild.name}**", ""]
        for r in plan.get("roles", []):
            resumen.append(f"• Rol: {r['nombre']} ({r['plantilla']})")
        for c in plan.get("categorias", []):
            canales = ", ".join(x["nombre"] for x in c.get("canales", []))
            resumen.append(f"• 📁 {c['nombre']}: {canales}")
        resumen.append(f"• Módulos: {', '.join(plan.get('modulos', []))}")
        resumen.append("")
        resumen.append("Revisa el plan y usa `/construir-aplicar` para crearlo, o `/construir-deshacer` para revertir.")
        await interaction.followup.send("\n".join(resumen))
        self.bot.planes_pendientes = getattr(self.bot, "planes_pendientes", {})
        self.bot.planes_pendientes[str(interaction.guild_id)] = plan

    @app_commands.command(name="construir-aplicar", description="Aplica el último plan propuesto")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def aplicar(self, interaction: discord.Interaction):
        plan = getattr(self.bot, "planes_pendientes", {}).get(str(interaction.guild_id))
        if not plan:
            await interaction.response.send_message("No hay plan pendiente. Usa `/construir` primero.", ephemeral=True)
            return
        await interaction.response.defer(thinking=True)

        def registrar(tipo: str, objeto_id: str):
            self.bot.loop.create_task(self.bot.db.registrar_constructor(str(interaction.guild_id), tipo, objeto_id))

        try:
            await constructor.aplicar(interaction.guild, plan, registrar)
        except constructor.PlanInvalido as error:
            await interaction.followup.send(f"❌ Plan inválido: {error}")
            return
        await interaction.followup.send(
            "✅ Plan aplicado. Puedes revertirlo con `/construir-deshacer`."
        )

    @app_commands.command(name="construir-deshacer", description="Revierte el último plan aplicado")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def deshacer(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        registro = await self.bot.db.registro_pendiente(str(interaction.guild_id))
        if not registro:
            await interaction.followup.send("No hay nada que deshacer.")
            return
        eliminados = await constructor.deshacer(interaction.guild, registro)
        await self.bot.db.marcar_deshecho(str(interaction.guild_id))
        await interaction.followup.send(f"↩️ Deshecho: {eliminados} objetos eliminados.")


async def setup(bot):
    await bot.add_cog(ConstructorCog(bot))
