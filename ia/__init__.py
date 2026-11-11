"""Capa de IA de la plataforma: cerebro (Gemini), RAG con citas, prompts y evaluaciones."""

from .cerebro import Cerebro, RespuestaIA, extraer_json, plan_por_defecto
from .rag import Fragmento, RAG

__all__ = ["Cerebro", "RespuestaIA", "Fragmento", "RAG", "extraer_json", "plan_por_defecto"]
