"""Núcleo del bot de Discord (fase 1).

Arranque: python -m bot.main
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import discord
from discord.ext import commands

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ia import Cerebro, RAG  # noqa: E402
from bot.config import Config  # noqa: E402
from bot.db import BaseDatos  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bot")

COGS_FASE1 = [
    "bot.cogs.bienvenida",
    "bot.cogs.moderacion",
    "bot.cogs.anti_spam",
    "bot.cogs.verificacion",
    "bot.cogs.logs",
    "bot.cogs.roles_botones",
    "bot.cogs.encuestas",
    "bot.cogs.tickets",
    "bot.cogs.pregunta",
    "bot.cogs.constructor_cog",
]


class PlataformaBot(commands.Bot):
    def __init__(self, config: Config):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.config = config
        self.db = BaseDatos(config.db_path)
        self.rag = RAG(config.db_path)
        self.cerebro = Cerebro(self.rag)

    async def setup_hook(self) -> None:
        await self.db.inicializar()
        for cog in COGS_FASE1:
            await self.load_extension(cog)
            log.info("Módulo cargado: %s", cog)
        await self.tree.sync()

    async def on_ready(self):
        log.info("Bot conectado como %s en %d servidores", self.user, len(self.guilds))


async def main() -> None:
    config = Config()
    if not config.valida:
        log.error("Falta DISCORD_TOKEN. Copia .env.example a .env y rellénalo.")
        return
    bot = PlataformaBot(config)
    async with bot:
        await bot.start(config.token)


if __name__ == "__main__":
    asyncio.run(main())
