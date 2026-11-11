"""Módulo de tienda: vende productos digitales dentro de Discord con PayPal.

Mejor que Shopify para comunidades: sin web externa, sin $29/mes, con
entrega automática por rol y panel de productos con botones de compra.
"""

from __future__ import annotations

import os
from urllib.parse import quote_plus

import discord
from discord import app_commands
from discord.ext import commands

PAYPAL_BASE = os.environ.get("PAYPAL_BASE", "https://api-m.sandbox.paypal.com")


def _link_pago(cliente_id: str, producto_nombre: str, precio: float, moneda: str = "USD") -> str:
    return (
        f"{PAYPAL_BASE.replace('api-m', 'www')}/checkoutnow?"
        f"cmd=_xclick&business={quote_plus(cliente_id)}"
        f"&item_name={quote_plus(producto_nombre)}&amount={precio:.2f}&currency_code={moneda}"
    )


class VistaTienda(discord.ui.View):
    def __init__(self, bot, servidor_id: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.servidor_id = servidor_id

    async def _productos(self) -> list[dict]:
        return await self.bot.db.productos_de(self.servidor_id)

    def _refrescar_botones(self, productos: list[dict]) -> None:
        self.clear_items()
        for p in productos[:20]:
            self.add_item(BotonComprar(p))

    @discord.ui.button(label="Ver catálogo", style=discord.ButtonStyle.primary, emoji="🛒", custom_id="tienda-catalogo")
    async def catalogo(self, interaction: discord.Interaction, boton: discord.ui.Button):
        productos = await self._productos()
        if not productos:
            await interaction.response.send_message("La tienda está vacía.", ephemeral=True)
            return
        lineas = "\n".join(f"**#{p['id']} · {p['nombre']}** — ${p['precio']:.2f}\n{p['descripcion']}" for p in productos[:10])
        await interaction.response.send_message(f"🛒 **Catálogo**\n{lineas}", ephemeral=True)


class BotonComprar(discord.ui.Button):
    def __init__(self, producto: dict):
        super().__init__(label=f"Comprar #{producto['id']}", style=discord.ButtonStyle.success, custom_id=f"tienda-comprar-{producto['id']}")
        self.producto = producto

    async def callback(self, interaction: discord.Interaction):
        p = self.producto
        vista = VistaCompra(p)
        await interaction.response.send_message(
            f"🛍️ **{p['nombre']}** — ${p['precio']:.2f}\n{p['descripcion']}\n\n"
            f"Si tienes un código de descuento, escríbelo abajo.",
            view=vista,
            ephemeral=True,
        )


class VistaCompra(discord.ui.View):
    def __init__(self, producto: dict):
        super().__init__(timeout=300)
        self.producto = producto

    @discord.ui.button(label="Pagar con PayPal", style=discord.ButtonStyle.primary, emoji="💳")
    async def pagar(self, interaction: discord.Interaction, boton: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        cliente_id = os.environ.get("PAYPAL_CLIENT_ID", "")
        if not cliente_id:
            await interaction.followup.send("El dueño aún no configuró PayPal. Avisa al staff.", ephemeral=True)
            return
        await interaction.followup.send(
            f"Completa tu pago aquí: {_link_pago(cliente_id, self.producto['nombre'], self.producto['precio'])}",
            ephemeral=True,
        )

    @discord.ui.button(label="Canjear código", style=discord.ButtonStyle.secondary)
    async def canjear(self, interaction: discord.Interaction, boton: discord.ui.Button):
        await interaction.response.send_message("Escribe tu código en el chat con el comando /tienda-codigo.", ephemeral=True)


class Tienda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tienda-añadir", description="Añade un producto a la tienda del servidor")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def añadir(self, interaction: discord.Interaction, nombre: str, precio: float, descripcion: str = "", entrega: str = ""):
        precio = max(0.5, round(precio, 2))
        id_ = await self.bot.db.añadir_producto(str(interaction.guild_id), nombre[:100], descripcion[:500], precio, entrega[:300])
        await interaction.response.send_message(f"✅ Producto #{id_} añadido: **{nombre}** — ${precio:.2f}")

    @app_commands.command(name="tienda-lista", description="Muestra los productos de la tienda")
    async def lista(self, interaction: discord.Interaction):
        productos = await self.bot.db.productos_de(str(interaction.guild_id))
        if not productos:
            await interaction.response.send_message("La tienda está vacía. Usa /tienda-añadir.", ephemeral=True)
            return
        lineas = "\n".join(f"#{p['id']} · **{p['nombre']}** — ${p['precio']:.2f}" for p in productos)
        await interaction.response.send_message(f"🛒 **Productos**\n{lineas}", ephemeral=True)

    @app_commands.command(name="tienda-quitar", description="Retira un producto de la tienda")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def quitar(self, interaction: discord.Interaction, id_producto: int):
        ok = await self.bot.db.eliminar_producto(str(interaction.guild_id), id_producto)
        await interaction.response.send_message("✅ Producto retirado." if ok else "No encontré ese producto.", ephemeral=True)

    @app_commands.command(name="tienda-panel", description="Publica el panel de la tienda en un canal")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def panel(self, interaction: discord.Interaction, canal: discord.TextChannel | None = None):
        destino = canal or interaction.channel
        vista = VistaTienda(self.bot, str(interaction.guild_id))
        productos = await vista._productos()
        vista._refrescar_botones(productos)
        await destino.send("🛒 **TIENDA** — pulsa para ver el catálogo y comprar:", view=vista)
        await interaction.response.send_message(f"✅ Panel publicado en {destino.mention}", ephemeral=True)

    @app_commands.command(name="tienda-descuento", description="Crea un código de descuento (porcentaje 1-90)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def descuento(self, interaction: discord.Interaction, codigo: str, porcentaje: int, maximo_usos: int = 0):
        porcentaje = max(1, min(90, porcentaje))
        await self.bot.db.crear_codigo(str(interaction.guild_id), codigo, porcentaje, maximo_usos)
        await interaction.response.send_message(f"✅ Código **{codigo.upper()}** creado: {porcentaje}% de descuento.", ephemeral=True)

    @app_commands.command(name="tienda-codigo", description="Valida tu código de descuento")
    async def codigo(self, interaction: discord.Interaction, codigo: str):
        porcentaje = await self.bot.db.usar_codigo(str(interaction.guild_id), codigo)
        if porcentaje is None:
            await interaction.response.send_message("❌ Código inválido o agotado.", ephemeral=True)
        else:
            await interaction.response.send_message(f"✅ Código aplicado: {porcentaje}% de descuento en tu próxima compra.", ephemeral=True)

    @app_commands.command(name="tienda-ventas", description="Ventas de la tienda de este servidor")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ventas(self, interaction: discord.Interaction):
        ventas = await self.bot.db.ventas_tienda_de(str(interaction.guild_id))
        total = sum(v["monto"] for v in ventas if v["estado"] == "pagada")
        await interaction.response.send_message(f"💰 {len(ventas)} ventas · ${total:.2f} cobrado", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Tienda(bot))
