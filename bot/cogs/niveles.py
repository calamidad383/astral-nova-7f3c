"""Módulo de niveles y XP con roles por nivel."""

from __future__ import annotations

import time

import discord
from discord import app_commands
from discord.ext import commands

ENFRIAMIENTO = 60.0
XP_POR_MENSAJE = 5
XP_POR_NIVEL = 100
ROLES_NIVEL = {5: "Nivel 5", 10: "Nivel 10", 25: "Nivel 25", 50: "Nivel 50"}


class Niveles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ultimo_xp: dict[tuple[int, int], float] = {}

    @commands.Cog.listener()
    async def on_message(self, mensaje: discord.Message):
        if mensaje.author.bot or not mensaje.guild:
            return
        if not await self.bot.db.modulo_activo(str(mensaje.guild.id), "niveles"):
            return
        clave = (mensaje.guild.id, mensaje.author.id)
        ahora = time.monotonic()
        if ahora - self.ultimo_xp.get(clave, 0) < ENFRIAMIENTO:
            return
        self.ultimo_xp[clave] = ahora
        xp = await self.bot.db.añadir_xp(str(mensaje.guild.id), str(mensaje.author.id), XP_POR_MENSAJE)
        nivel = xp // XP_POR_NIVEL
        nombre_rol = ROLES_NIVEL.get(nivel)
        if nombre_rol:
            rol = discord.utils.get(mensaje.guild.roles, name=nombre_rol)
            if rol is None:
                rol = await mensaje.guild.create_role(name=nombre_rol, colour=discord.Color.gold(), reason="Recompensa de nivel")
            if rol not in mensaje.author.roles:
                await mensaje.author.add_roles(rol, reason=f"Alcanzó {nombre_rol}")
                await mensaje.channel.send(f"🎉 {mensaje.author.mention} alcanzó {nombre_rol}!", delete_after=15)

    @app_commands.command(name="nivel", description="Muestra tu nivel y experiencia")
    async def nivel(self, interaction: discord.Interaction):
        top = await self.bot.db.top_niveles(str(interaction.guild_id), 1000)
        xp = next((t["xp"] for t in top if t["usuario_id"] == str(interaction.user.id)), 0)
        nivel = xp // XP_POR_NIVEL
        await interaction.response.send_message(
            f"📊 Nivel {nivel} con {xp} XP. Faltan {XP_POR_NIVEL - (xp % XP_POR_NIVEL)} XP para el siguiente nivel."
        )

    @app_commands.command(name="clasificacion", description="Tabla de clasificación del servidor")
    async def clasificacion(self, interaction: discord.Interaction):
        top = await self.bot.db.top_niveles(str(interaction.guild_id), 10)
        lineas = [
            f"{i + 1}. <@{t['usuario_id']}> — {t['xp']} XP (nivel {t['xp'] // XP_POR_NIVEL})"
            for i, t in enumerate(top)
        ]
        await interaction.response.send_message("🏆 **Clasificación**\n" + ("\n".join(lineas) or "Sin datos todavía."))


async def setup(bot):
    await bot.add_cog(Niveles(bot))
