"""Pruebas del módulo de tienda (base de datos, sin Discord)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.db import BaseDatos  # noqa: E402


async def test_ciclo_completo_de_tienda(tmp_path):
    db = BaseDatos(str(tmp_path / "t.db"))
    await db.inicializar()
    srv = "srv-tienda"

    id_prod = await db.añadir_producto(srv, "Pack de plantillas", "10 plantillas Notion", 12.0, "rol:Comprador")
    productos = await db.productos_de(srv)
    assert len(productos) == 1
    assert productos[0]["precio"] == 12.0

    porcentaje = await db.usar_codigo(srv, "LANZAMIENTO")
    assert porcentaje is None

    await db.crear_codigo(srv, "lanzamiento", 20, maximo_usos=1)
    assert await db.usar_codigo(srv, "lanzamiento") == 20
    assert await db.usar_codigo(srv, "LANZAMIENTO") is None

    venta = await db.registrar_venta_tienda(srv, id_prod, "usuario1", 9.6)
    await db.marcar_venta_pagada(venta)
    ventas = await db.ventas_tienda_de(srv)
    assert len(ventas) == 1
    assert ventas[0]["estado"] == "pagada"

    assert await db.eliminar_producto(srv, id_prod)
    assert await db.productos_de(srv) == []
    producto = await db.producto(srv, id_prod)
    assert producto["activo"] == 0


async def test_tienda_aislada_por_servidor(tmp_path):
    db = BaseDatos(str(tmp_path / "t.db"))
    await db.inicializar()
    await db.añadir_producto("srv-a", "Producto A", "", 5.0)
    await db.añadir_producto("srv-b", "Producto B", "", 7.0)
    assert [p["nombre"] for p in await db.productos_de("srv-a")] == ["Producto A"]
    assert [p["nombre"] for p in await db.productos_de("srv-b")] == ["Producto B"]
