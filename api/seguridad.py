"""Sistema de ciberseguridad: ban permanente de atacantes, límite de peticiones
y registro de eventos de seguridad.

Reglas:
- 5 intentos fallidos de autenticación desde una IP = **ban permanente**.
- Los IPs baneados se rechazan antes de llegar a cualquier endpoint.
- Cada evento queda registrado para el panel del dueño.
"""

from __future__ import annotations

import sqlite3
import time
from collections import defaultdict, deque
from pathlib import Path

MAX_INTENTOS_FALLIDOS = 5
VENTANA_RATE = 60.0
MAX_PETICIONES_POR_VENTANA = 120


class Seguridad:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._rate: dict[str, deque] = defaultdict(lambda: deque(maxlen=MAX_PETICIONES_POR_VENTANA * 2))
        con = sqlite3.connect(self.db_path)
        try:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS bans_seguridad (
                    ip TEXT PRIMARY KEY,
                    motivo TEXT NOT NULL,
                    permanente INTEGER NOT NULL DEFAULT 1,
                    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS eventos_seguridad (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    ip TEXT NOT NULL DEFAULT '',
                    detalle TEXT NOT NULL DEFAULT '',
                    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            con.commit()
        finally:
            con.close()

    def _con(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    # ------------------------------------------------ bans

    def esta_baneada(self, ip: str) -> bool:
        con = self._con()
        try:
            fila = con.execute("SELECT 1 FROM bans_seguridad WHERE ip = ?", (ip,)).fetchone()
            return fila is not None
        finally:
            con.close()

    def banear(self, ip: str, motivo: str, permanente: bool = True) -> None:
        con = self._con()
        try:
            con.execute(
                "INSERT OR REPLACE INTO bans_seguridad (ip, motivo, permanente) VALUES (?, ?, ?)",
                (ip, motivo, int(permanente)),
            )
            con.execute(
                "INSERT INTO eventos_seguridad (tipo, ip, detalle) VALUES ('ban', ?, ?)", (ip, motivo)
            )
            con.commit()
        finally:
            con.close()

    def desbanear(self, ip: str) -> bool:
        con = self._con()
        try:
            cur = con.execute("DELETE FROM bans_seguridad WHERE ip = ?", (ip,))
            con.commit()
            return cur.rowcount > 0
        finally:
            con.close()

    def bans(self) -> list[dict]:
        con = self._con()
        try:
            return [dict(f) for f in con.execute("SELECT * FROM bans_seguridad ORDER BY creado_en DESC")]
        finally:
            con.close()

    # ------------------------------------------------ intentos fallidos

    def registrar_intento_fallido(self, ip: str) -> bool:
        """Devuelve True si con este intento se decreta el ban permanente."""
        con = self._con()
        try:
            con.execute(
                "INSERT INTO eventos_seguridad (tipo, ip, detalle) VALUES ('intento_fallido', ?, '')", (ip,)
            )
            con.commit()
            recientes = con.execute(
                "SELECT COUNT(*) FROM eventos_seguridad WHERE tipo = 'intento_fallido' AND ip = ? AND creado_en > datetime('now', '-15 minutes')",
                (ip,),
            ).fetchone()[0]
        finally:
            con.close()
        if recientes >= MAX_INTENTOS_FALLIDOS:
            self.banear(ip, f"{MAX_INTENTOS_FALLIDOS} intentos fallidos de acceso en 15 minutos: atacante baneado permanentemente")
            return True
        return False

    # ------------------------------------------------ rate limit

    def permitir(self, ip: str) -> bool:
        ahora = time.monotonic()
        ventana = self._rate[ip]
        ventana.append(ahora)
        while ventana and ahora - ventana[0] > VENTANA_RATE:
            ventana.popleft()
        return len(ventana) <= MAX_PETICIONES_POR_VENTANA

    # ------------------------------------------------ eventos

    def registrar_evento(self, tipo: str, ip: str = "", detalle: str = "") -> None:
        con = self._con()
        try:
            con.execute("INSERT INTO eventos_seguridad (tipo, ip, detalle) VALUES (?, ?, ?)", (tipo, ip, detalle))
            con.commit()
        finally:
            con.close()

    def eventos(self, limite: int = 50) -> list[dict]:
        con = self._con()
        try:
            return [dict(f) for f in con.execute("SELECT * FROM eventos_seguridad ORDER BY id DESC LIMIT ?", (limite,))]
        finally:
            con.close()
