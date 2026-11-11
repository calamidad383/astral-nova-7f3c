"""Configuración del bot desde variables de entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _cargar_dotenv(ruta: Path) -> None:
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        clave, valor = clave.strip(), valor.strip().strip('"').strip("'")
        os.environ.setdefault(clave, valor)


_cargar_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass
class Config:
    token: str = field(default_factory=lambda: os.environ.get("DISCORD_TOKEN", ""))
    cliente_id: str = field(default_factory=lambda: os.environ.get("DISCORD_CLIENT_ID", ""))
    db_path: str = field(default_factory=lambda: os.environ.get("DATABASE_PATH", "data/plataforma.db"))
    api_url: str = field(default_factory=lambda: os.environ.get("API_URL", "http://localhost:8000"))

    @property
    def valida(self) -> bool:
        return bool(self.token)
