"""Base de datos compartida del bot (SQLite).

Fase 1 usa SQLite; la migración a PostgreSQL está prevista en la fase 4.
Todas las tablas se crean de forma idempotente al arrancar.
"""

from __future__ import annotations

import aiosqlite
from pathlib import Path

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS modulos_activos (
    servidor_id TEXT NOT NULL,
    modulo TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (servidor_id, modulo)
);

CREATE TABLE IF NOT EXISTS configuracion_modulo (
    servidor_id TEXT NOT NULL,
    modulo TEXT NOT NULL,
    clave TEXT NOT NULL,
    valor TEXT NOT NULL,
    PRIMARY KEY (servidor_id, modulo, clave)
);

CREATE TABLE IF NOT EXISTS casos_moderacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servidor_id TEXT NOT NULL,
    usuario_id TEXT NOT NULL,
    moderador_id TEXT NOT NULL,
    tipo TEXT NOT NULL,
    motivo TEXT NOT NULL DEFAULT '',
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servidor_id TEXT NOT NULL,
    canal_id TEXT NOT NULL,
    usuario_id TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'abierto',
    prioridad TEXT NOT NULL DEFAULT 'normal',
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
    cerrado_en TEXT
);

CREATE TABLE IF NOT EXISTS advertencias_verificacion (
    usuario_id TEXT PRIMARY KEY,
    servidor_id TEXT NOT NULL,
    verificada INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS registro_constructor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servidor_id TEXT NOT NULL,
    tipo TEXT NOT NULL,
    objeto_id TEXT NOT NULL,
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
    deshecho INTEGER NOT NULL DEFAULT 0
);
"""


class BaseDatos:
    def __init__(self, ruta: str):
        self.ruta = ruta
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)

    def _con(self) -> aiosqlite.Connection:
        return aiosqlite.connect(self.ruta)

    async def inicializar(self) -> None:
        async with self._con() as con:
            await con.executescript(_ESQUEMA)
            await con.commit()

    async def modulo_activo(self, servidor_id: str, modulo: str) -> bool:
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            fila = await con.execute_fetchall(
                "SELECT activo FROM modulos_activos WHERE servidor_id = ? AND modulo = ?",
                (servidor_id, modulo),
            )
        if not fila:
            return True
        return bool(fila[0]["activo"])

    async def fijar_modulo(self, servidor_id: str, modulo: str, activo: bool) -> None:
        async with self._con() as con:
            await con.execute(
                "INSERT OR REPLACE INTO modulos_activos (servidor_id, modulo, activo) VALUES (?, ?, ?)",
                (servidor_id, modulo, int(activo)),
            )
            await con.commit()

    async def registrar_caso(
        self, servidor_id: str, usuario_id: str, moderador_id: str, tipo: str, motivo: str = ""
    ) -> int:
        async with self._con() as con:
            cur = await con.execute(
                "INSERT INTO casos_moderacion (servidor_id, usuario_id, moderador_id, tipo, motivo) VALUES (?, ?, ?, ?, ?)",
                (servidor_id, usuario_id, moderador_id, tipo, motivo),
            )
            await con.commit()
            return cur.lastrowid

    async def casos_de(self, servidor_id: str, usuario_id: str) -> list[dict]:
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            filas = await con.execute_fetchall(
                "SELECT * FROM casos_moderacion WHERE servidor_id = ? AND usuario_id = ? ORDER BY id DESC",
                (servidor_id, usuario_id),
            )
        return [dict(f) for f in filas]

    async def crear_ticket(self, servidor_id: str, canal_id: str, usuario_id: str) -> int:
        async with self._con() as con:
            cur = await con.execute(
                "INSERT INTO tickets (servidor_id, canal_id, usuario_id) VALUES (?, ?, ?)",
                (servidor_id, canal_id, usuario_id),
            )
            await con.commit()
            return cur.lastrowid

    async def cerrar_ticket(self, servidor_id: str, canal_id: str) -> bool:
        async with self._con() as con:
            cur = await con.execute(
                "UPDATE tickets SET estado = 'cerrado', cerrado_en = CURRENT_TIMESTAMP WHERE servidor_id = ? AND canal_id = ? AND estado = 'abierto'",
                (servidor_id, canal_id),
            )
            await con.commit()
            return cur.rowcount > 0

    async def registrar_constructor(self, servidor_id: str, tipo: str, objeto_id: str) -> None:
        async with self._con() as con:
            await con.execute(
                "INSERT INTO registro_constructor (servidor_id, tipo, objeto_id) VALUES (?, ?, ?)",
                (servidor_id, tipo, objeto_id),
            )
            await con.commit()

    async def registro_pendiente(self, servidor_id: str) -> list[tuple[str, str]]:
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            filas = await con.execute_fetchall(
                "SELECT tipo, objeto_id FROM registro_constructor WHERE servidor_id = ? AND deshecho = 0 ORDER BY id DESC",
                (servidor_id,),
            )
        return [(f["tipo"], f["objeto_id"]) for f in filas]

    async def marcar_deshecho(self, servidor_id: str) -> None:
        async with self._con() as con:
            await con.execute(
                "UPDATE registro_constructor SET deshecho = 1 WHERE servidor_id = ? AND deshecho = 0",
                (servidor_id,),
            )
            await con.commit()
