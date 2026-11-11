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

CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servidor_id TEXT NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    precio REAL NOT NULL,
    entrega TEXT NOT NULL DEFAULT '',
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS codigos_descuento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servidor_id TEXT NOT NULL,
    codigo TEXT NOT NULL,
    porcentaje INTEGER NOT NULL,
    usos INTEGER NOT NULL DEFAULT 0,
    maximo_usos INTEGER NOT NULL DEFAULT 0,
    UNIQUE (servidor_id, codigo)
);

CREATE TABLE IF NOT EXISTS ventas_tienda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servidor_id TEXT NOT NULL,
    producto_id INTEGER NOT NULL,
    comprador_id TEXT NOT NULL,
    monto REAL NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servidor_id TEXT NOT NULL,
    plan TEXT NOT NULL,
    monto REAL NOT NULL,
    moneda TEXT NOT NULL DEFAULT 'USD',
    tipo TEXT NOT NULL DEFAULT 'pago',
    origen TEXT NOT NULL DEFAULT 'manual',
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS niveles (
    servidor_id TEXT NOT NULL,
    usuario_id TEXT NOT NULL,
    xp INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (servidor_id, usuario_id)
);

CREATE TABLE IF NOT EXISTS recordatorios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servidor_id TEXT NOT NULL,
    canal_id TEXT NOT NULL,
    usuario_id TEXT NOT NULL,
    texto TEXT NOT NULL,
    cuando TEXT NOT NULL,
    hecho INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS anuncios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servidor_id TEXT NOT NULL,
    canal_id TEXT NOT NULL,
    texto TEXT NOT NULL,
    cuando TEXT NOT NULL,
    hecho INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servidor_id TEXT NOT NULL,
    datos TEXT NOT NULL,
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
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

    # ------------------------------------------------ negocio (panel del dueño)

    async def inicializar_negocio(self) -> None:
        pass  # las tablas ya se crean en inicializar()

    async def registrar_pago(
        self, servidor_id: str, plan: str, monto: float, tipo: str = "pago", origen: str = "manual", moneda: str = "USD"
    ) -> int:
        async with self._con() as con:
            cur = await con.execute(
                "INSERT INTO pagos (servidor_id, plan, monto, tipo, origen, moneda) VALUES (?, ?, ?, ?, ?, ?)",
                (servidor_id, plan, monto, tipo, origen, moneda),
            )
            await con.commit()
            return cur.lastrowid

    async def resumen_negocio(self, servidor_id: str | None = None) -> dict:
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            filtro = "WHERE servidor_id = ?" if servidor_id else ""
            parametros = (servidor_id,) if servidor_id else ()
            filas = await con.execute_fetchall(
                f"SELECT tipo, plan, monto, moneda, creado_en FROM pagos {filtro} ORDER BY id DESC LIMIT 100",
                parametros,
            )
        pagos = [dict(f) for f in filas]
        ingresos = sum(p["monto"] for p in pagos if p["tipo"] == "pago")
        reembolsos = sum(p["monto"] for p in pagos if p["tipo"] == "reembolso")
        por_plan: dict[str, float] = {}
        for p in pagos:
            if p["tipo"] == "pago":
                por_plan[p["plan"]] = por_plan.get(p["plan"], 0.0) + p["monto"]
        return {
            "ingresos_totales": round(ingresos, 2),
            "reembolsos": round(reembolsos, 2),
            "neto": round(ingresos - reembolsos, 2),
            "ventas": sum(1 for p in pagos if p["tipo"] == "pago"),
            "por_plan": por_plan,
            "transacciones": pagos[:30],
            "moneda": "USD",
        }

    # ------------------------------------------------ niveles

    async def añadir_xp(self, servidor_id: str, usuario_id: str, cantidad: int) -> int:
        async with self._con() as con:
            await con.execute(
                "INSERT INTO niveles (servidor_id, usuario_id, xp) VALUES (?, ?, ?) "
                "ON CONFLICT(servidor_id, usuario_id) DO UPDATE SET xp = xp + ?",
                (servidor_id, usuario_id, cantidad, cantidad),
            )
            await con.commit()
            filas = await con.execute_fetchall(
                "SELECT xp FROM niveles WHERE servidor_id = ? AND usuario_id = ?", (servidor_id, usuario_id)
            )
            return filas[0][0]

    async def top_niveles(self, servidor_id: str, limite: int = 10) -> list[dict]:
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            filas = await con.execute_fetchall(
                "SELECT usuario_id, xp FROM niveles WHERE servidor_id = ? ORDER BY xp DESC LIMIT ?",
                (servidor_id, limite),
            )
        return [dict(f) for f in filas]

    # ------------------------------------------------ recordatorios y anuncios

    async def crear_recordatorio(self, servidor_id: str, canal_id: str, usuario_id: str, texto: str, cuando: str) -> int:
        async with self._con() as con:
            cur = await con.execute(
                "INSERT INTO recordatorios (servidor_id, canal_id, usuario_id, texto, cuando) VALUES (?, ?, ?, ?, ?)",
                (servidor_id, canal_id, usuario_id, texto, cuando),
            )
            await con.commit()
            return cur.lastrowid

    async def recordatorios_pendientes(self, ahora_iso: str) -> list[dict]:
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            filas = await con.execute_fetchall(
                "SELECT * FROM recordatorios WHERE hecho = 0 AND cuando <= ?", (ahora_iso,)
            )
        return [dict(f) for f in filas]

    async def marcar_recordatorio(self, id_: int) -> None:
        async with self._con() as con:
            await con.execute("UPDATE recordatorios SET hecho = 1 WHERE id = ?", (id_,))
            await con.commit()

    async def programar_anuncio(self, servidor_id: str, canal_id: str, texto: str, cuando: str) -> int:
        async with self._con() as con:
            cur = await con.execute(
                "INSERT INTO anuncios (servidor_id, canal_id, texto, cuando) VALUES (?, ?, ?, ?)",
                (servidor_id, canal_id, texto, cuando),
            )
            await con.commit()
            return cur.lastrowid

    async def anuncios_pendientes(self, ahora_iso: str) -> list[dict]:
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            filas = await con.execute_fetchall(
                "SELECT * FROM anuncios WHERE hecho = 0 AND cuando <= ?", (ahora_iso,)
            )
        return [dict(f) for f in filas]

    async def marcar_anuncio(self, id_: int) -> None:
        async with self._con() as con:
            await con.execute("UPDATE anuncios SET hecho = 1 WHERE id = ?", (id_,))
            await con.commit()

    # ------------------------------------------------ copias de seguridad

    async def guardar_backup(self, servidor_id: str, datos: str) -> int:
        async with self._con() as con:
            cur = await con.execute("INSERT INTO backups (servidor_id, datos) VALUES (?, ?)", (servidor_id, datos))
            await con.commit()
            return cur.lastrowid

    async def backups_de(self, servidor_id: str) -> list[dict]:
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            filas = await con.execute_fetchall(
                "SELECT id, creado_en FROM backups WHERE servidor_id = ? ORDER BY id DESC LIMIT 20", (servidor_id,)
            )
        return [dict(f) for f in filas]

    # ------------------------------------------------ tienda

    async def añadir_producto(
        self, servidor_id: str, nombre: str, descripcion: str, precio: float, entrega: str = ""
    ) -> int:
        async with self._con() as con:
            cur = await con.execute(
                "INSERT INTO productos (servidor_id, nombre, descripcion, precio, entrega) VALUES (?, ?, ?, ?, ?)",
                (servidor_id, nombre, descripcion, precio, entrega),
            )
            await con.commit()
            return cur.lastrowid

    async def productos_de(self, servidor_id: str, solo_activos: bool = True) -> list[dict]:
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            filtro = "WHERE servidor_id = ? AND activo = 1" if solo_activos else "WHERE servidor_id = ?"
            filas = await con.execute_fetchall(
                f"SELECT * FROM productos {filtro} ORDER BY id DESC", (servidor_id,)
            )
        return [dict(f) for f in filas]

    async def producto(self, servidor_id: str, id_: int) -> dict | None:
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            filas = await con.execute_fetchall(
                "SELECT * FROM productos WHERE servidor_id = ? AND id = ?", (servidor_id, id_)
            )
        return dict(filas[0]) if filas else None

    async def eliminar_producto(self, servidor_id: str, id_: int) -> bool:
        async with self._con() as con:
            cur = await con.execute(
                "UPDATE productos SET activo = 0 WHERE servidor_id = ? AND id = ?", (servidor_id, id_)
            )
            await con.commit()
            return cur.rowcount > 0

    async def crear_codigo(self, servidor_id: str, codigo: str, porcentaje: int, maximo_usos: int = 0) -> int:
        async with self._con() as con:
            cur = await con.execute(
                "INSERT OR REPLACE INTO codigos_descuento (servidor_id, codigo, porcentaje, maximo_usos) VALUES (?, ?, ?, ?)",
                (servidor_id, codigo.upper(), porcentaje, maximo_usos),
            )
            await con.commit()
            return cur.lastrowid

    async def usar_codigo(self, servidor_id: str, codigo: str) -> int | None:
        """Devuelve el porcentaje si el código es utilizable y registra el uso."""
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            filas = await con.execute_fetchall(
                "SELECT * FROM codigos_descuento WHERE servidor_id = ? AND codigo = ?",
                (servidor_id, codigo.upper()),
            )
            if not filas:
                return None
            fila = dict(filas[0])
            if fila["maximo_usos"] and fila["usos"] >= fila["maximo_usos"]:
                return None
            await con.execute(
                "UPDATE codigos_descuento SET usos = usos + 1 WHERE servidor_id = ? AND codigo = ?",
                (servidor_id, codigo.upper()),
            )
            await con.commit()
            return fila["porcentaje"]

    async def registrar_venta_tienda(self, servidor_id: str, producto_id: int, comprador_id: str, monto: float) -> int:
        async with self._con() as con:
            cur = await con.execute(
                "INSERT INTO ventas_tienda (servidor_id, producto_id, comprador_id, monto) VALUES (?, ?, ?, ?)",
                (servidor_id, producto_id, comprador_id, monto),
            )
            await con.commit()
            return cur.lastrowid

    async def marcar_venta_pagada(self, id_: int) -> None:
        async with self._con() as con:
            await con.execute("UPDATE ventas_tienda SET estado = 'pagada' WHERE id = ?", (id_,))
            await con.commit()

    async def ventas_tienda_de(self, servidor_id: str) -> list[dict]:
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            filas = await con.execute_fetchall(
                "SELECT * FROM ventas_tienda WHERE servidor_id = ? ORDER BY id DESC LIMIT 100", (servidor_id,)
            )
        return [dict(f) for f in filas]

    async def obtener_backup(self, servidor_id: str, id_: int) -> dict | None:
        async with self._con() as con:
            con.row_factory = aiosqlite.Row
            filas = await con.execute_fetchall(
                "SELECT * FROM backups WHERE servidor_id = ? AND id = ?", (servidor_id, id_)
            )
        return dict(filas[0]) if filas else None
