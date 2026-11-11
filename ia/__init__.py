"""Capa de IA de la plataforma: motor propio local (sin APIs externas), RAG con citas, prompts y evaluaciones."""

from .cerebro import Cerebro, RespuestaIA
from .motor import MotorLocal
from .rag import Fragmento, RAG

__all__ = ["Cerebro", "RespuestaIA", "MotorLocal", "Fragmento", "RAG"]
