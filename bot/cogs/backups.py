"""Módulo de copias de seguridad: guarda y restaura estructura del servidor."""

from __future__ import annotations

import json

import discord
from discord import app_commands
from discord.ext import commands


class Backups(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="backup-crear", description="Guarda una copia de la estructura del servidor")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def backup_crear(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        datos = {
            "roles": [{"nombre": r.name, "color": str(r.colour)} for r in guild.roles if r.name != "@everyone"],
            "categorias": [
                {
                    "nombre": c.name,
                    "canales": [
                        {"nombre": ch.name, "tipo": "voz" if isinstance(ch, discord.VoiceChannel) else "texto"}
                        for ch in c.channels
                    ],
                }
                for c in guild.categories
            ],
        }
        id_ = await self.bot.db.guardar_backup(str(guild.id), json.dumps(datos, ensure_ascii=False))
        await interaction.followup.send(
            f"💾 Copia #{id_} guardada ({len(datos['roles'])} roles, {len(datos['categorias'])} categorías)."
        )

    @app_commands.command(name="backup-lista", description="Lista las copias de seguridad guardadas")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def backup_lista(self, interaction: discord.Interaction):
        copias = await self.bot.db.backups_de(str(interaction.guild_id))
        if not copias:
            await interaction.response.send_message("No hay copias guardadas. Usa /backup-crear.", ephemeral=True)
            return
        lineas = [f"• #{c['id']} — {c['creado_en']}" for c in copias]
        await interaction.response.send_message("💾 Copias disponibles:\n" + "\n".join(lineas), ephemeral=True)

    @app_commands.command(name="backup-restaurar", description="Restaura la estructura de una copia (crea lo que falte)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def backup_restaurar(self, interaction: discord.Interaction, id_copia: int):
        await interaction.response.defer(ephemeral=True)
        copia = await self.bot.db.obtener_backup(str(interaction.guild_id), id_copia)
        if not copia:
            await interaction.followup.send("Copia no encontrada. Usa /backup-lista.")
            return
        datos = json.loads(copia["datos"])
        creados = 0
        for rol in datos.get("roles", []):
            if discord.utils.get(interaction.guild.roles, name=rol["nombre"]) is None:
                color = discord.Colour.from_str(rol["color"]) if rol["color"].startswith("#") else discord.Color.default()
                await interaction.guild.create_role(name=rol["nombre"], colour=color, reason="Restaurar backup")
                creados += 1
        for categoria in datos.get("categorias", []):
            cat = discord.utils.get(interaction.guild.categories, name=categoria["nombre"])
            if cat is None:
                cat = await interaction.guild.create_category(categoria["nombre"], reason="Restaurar backup")
                creados += 1
            for canal in categoria.get("canales", []):
                if discord.utils.get(cat.channels, name=canal["nombre"]) is None:
                    if canal["tipo"] == "voz":
                        await interaction.guild.create_voice_channel(canal["nombre"], category=cat, reason="Restaurar backup")
                    else:
                        await interaction.guild.create_text_channel(canal["nombre"], category=cat, reason="Restaurar backup")
                    creados += 1
        await interaction.followup.send(f"✅ Restauración terminada: {creados} objetos creados.")


async def setup(bot):
    await bot.add_cog(Backups(bot))
