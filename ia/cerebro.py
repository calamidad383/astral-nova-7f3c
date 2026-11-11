"""Cerebro de IA: cliente Gemini por API REST con degradación elegante.

- Usa un modelo rápido para respuestas frecuentes y uno potente para el
  constructor (ver .env.example).
- Si no hay GEMINI_API_KEY, funciona en "modo sin IA": el RAG responde con
  fuentes y el constructor devuelve un plan por plantilla. Nunca se inventa.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

import httpx

from . import prompts
from .rag import RAG

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


@dataclass
class RespuestaIA:
    texto: str
    fuentes: list[str] = field(default_factory=list)
    modo: str = "ia"  # "ia" | "sin-ia"


class Cerebro:
    def __init__(self, rag: RAG, api_key: str | None = None):
        self.rag = rag
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.modelo = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        self.modelo_pro = os.environ.get("GEMINI_MODEL_PRO", "gemini-2.5-pro")

    @property
    def disponible(self) -> bool:
        return bool(self.api_key)

    async def _generar(self, prompt_sistema: str, usuario: str, pro: bool = False) -> str:
        if not self.disponible:
            raise RuntimeError("IA no configurada: falta GEMINI_API_KEY")
        modelo = self.modelo_pro if pro else self.modelo
        url = f"{GEMINI_BASE}/models/{modelo}:generateContent"
        cuerpo = {
            "system_instruction": {"parts": [{"text": prompt_sistema}]},
            "contents": [{"role": "user", "parts": [{"text": usuario}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048},
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, params={"key": self.api_key}, json=cuerpo)
            r.raise_for_status()
            datos = r.json()
        candidatos = datos.get("candidates", [])
        if not candidatos:
            return ""
        partes = candidatos[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in partes).strip()

    async def responder_pregunta(self, servidor_id: str, nombre_servidor: str, pregunta: str) -> RespuestaIA:
        contexto, fuentes = self.rag.contexto(servidor_id, pregunta)
        if not fuentes and not self.disponible:
            return RespuestaIA(
                "No tengo esa información en la base de conocimiento del servidor. "
                "Derivaré tu pregunta a un moderador.",
                modo="sin-ia",
            )
        if not self.disponible:
            if not fuentes:
                return RespuestaIA(
                    "No tengo esa información en la base de conocimiento del servidor. "
                    "Derivaré tu pregunta a un moderador.",
                    modo="sin-ia",
                )
            frag = self.rag.buscar(servidor_id, pregunta, 1)[0]
            return RespuestaIA(
                f"Según la base de conocimiento:\n\n**{frag.titulo}**\n{frag.contenido}\n\nFuentes: {frag.id}",
                fuentes=[frag.id],
                modo="sin-ia",
            )
        sistema = prompts.PREGUNTA_SISTEMA.format(servidor=nombre_servidor)
        usuario = f"Base de conocimiento:\n{contexto or '(vacía)'}\n\nPregunta: {pregunta}"
        texto = await self._generar(sistema, usuario)
        return RespuestaIA(texto, fuentes=fuentes)

    async def sugerir_moderacion(self, servidor_id: str, nombre_servidor: str, mensaje: str, contexto: str = "") -> dict:
        if not self.disponible:
            return {"accion": "nada", "motivo": "IA no configurada: revisión manual", "confianza": 0.0}
        sistema = prompts.MODERACION_SISTEMA.format(servidor=nombre_servidor)
        usuario = f"Contexto reciente:\n{contexto or '(ninguno)'}\n\nMensaje a evaluar:\n{mensaje}"
        texto = await self._generar(sistema, usuario)
        try:
            datos = json.loads(extraer_json(texto))
        except (ValueError, TypeError):
            return {"accion": "nada", "motivo": "Respuesta de IA no interpretable", "confianza": 0.0}
        if datos.get("accion") not in {"nada", "advertencia", "eliminar_mensaje", "silenciar", "escalar"}:
            datos["accion"] = "nada"
        return datos

    async def plan_constructor(self, descripcion: str, max_roles: int = 30, max_canales: int = 100) -> dict:
        if not self.disponible:
            return plan_por_defecto(descripcion)
        sistema = prompts.CONSTRUCTOR_SISTEMA.format(max_roles=max_roles, max_canales=max_canales)
        texto = await self._generar(sistema, descripcion, pro=True)
        try:
            return json.loads(extraer_json(texto))
        except (ValueError, TypeError):
            return plan_por_defecto(descripcion)

    async def resumir(self, servidor_id: str, nombre_servidor: str, mensajes: list[str]) -> str:
        if not self.disponible:
            return "(IA no configurada: no hay resumen automático)"
        sistema = prompts.RESUMEN_SISTEMA.format(servidor=nombre_servidor)
        usuario = "\n".join(mensajes[-100:])
        return await self._generar(sistema, usuario)


def extraer_json(texto: str) -> str:
    cerca = texto.find("{")
    final = texto.rfind("}")
    if cerca == -1 or final == -1 or final <= cerca:
        raise ValueError("Sin JSON en la respuesta")
    return re.sub(r"```(?:json)?|```", "", texto[cerca : final + 1]).strip()


def plan_por_defecto(descripcion: str) -> dict:
    """Plan mínimo seguro cuando la IA no está disponible o falla."""
    tema = (descripcion or "comunidad").strip()[:30] or "comunidad"
    return {
        "roles": [
            {"nombre": "Moderador", "color": "#F59E0B", "plantilla": "moderador"},
            {"nombre": "Miembro", "color": "#5865F2", "plantilla": "miembro"},
        ],
        "categorias": [
            {
                "nombre": "INFORMACIÓN",
                "canales": [
                    {"nombre": "bienvenida", "tipo": "texto", "solo_lectura": True},
                    {"nombre": "reglas", "tipo": "texto", "solo_lectura": True},
                    {"nombre": "anuncios", "tipo": "texto", "solo_lectura": True},
                ],
            },
            {
                "nombre": "GENERAL",
                "canales": [
                    {"nombre": "general", "tipo": "texto"},
                    {"nombre": "soporte", "tipo": "texto"},
                ],
            },
        ],
        "mensajes": [
            {
                "canal": "reglas",
                "contenido": f"Reglas de {tema}:\n1. Respeto ante todo.\n2. Sin spam ni publicidad.\n3. Contenido adecuado.",
            },
            {
                "canal": "bienvenida",
                "contenido": f"¡Bienvenido a {tema}! Lee #reglas y preséntate en #general.",
            },
        ],
        "modulos": ["bienvenida", "tickets", "anti_spam", "encuestas"],
    }
