"""Módulo de bienvenida y despedida."""

from __future__ import annotations

import discord
from discord.ext import commands


class Bienvenida(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, miembro: discord.Member):
        if not await self.bot.db.modulo_activo(str(miembro.guild.id), "bienvenida"):
            return
        canal = miembro.guild.system_channel
        if canal:
            embed = discord.Embed(
                title=f"¡Bienvenido, {miembro.name}!",
                description=f"Lee las reglas y preséntate. Eres el miembro #{miembro.guild.member_count}.",
                color=discord.Color.blurple(),
            )
            embed.set_thumbnail(url=miembro.display_avatar.url)
            await canal.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, miembro: discord.Member):
        if not await self.bot.db.modulo_activo(str(miembro.guild.id), "bienvenida"):
            return
        canal = miembro.guild.system_channel
        if canal:
            await canal.send(f"{miembro.name} ha salido del servidor. ¡Hasta pronto!")


async def setup(bot):
    await bot.add_cog(Bienvenida(bot))
