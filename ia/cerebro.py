"""Cerebro de IA de la plataforma: motor propio local, entrenado sin APIs externas.

Mantiene la interfaz asíncrona que usan el bot y la API. Todo el
razonamiento ocurre en `ia/motor.py` con datos del propio servidor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .motor import MotorLocal
from .rag import RAG


@dataclass
class RespuestaIA:
    texto: str
    fuentes: list[str] = field(default_factory=list)
    modo: str = "local"


class Cerebro:
    """Fachada asíncrona del motor local."""

    def __init__(self, rag: RAG, db_path: str | None = None):
        self.rag = rag
        self.motor = MotorLocal(rag, db_path or getattr(rag, "db_path", "data/plataforma.db"))

    @property
    def disponible(self) -> bool:
        return True

    def entrenar(self, servidor_id: str | None = None) -> dict:
        entrenamiento = self.motor.entrenar(servidor_id)
        return {"documentos": entrenamiento.documentos, "terminos": entrenamiento.terminos}

    def aprender(self, servidor_id: str, id_doc: str, util: bool) -> float:
        return self.motor.aprender(servidor_id, id_doc, util)

    async def responder_pregunta(self, servidor_id: str, nombre_servidor: str, pregunta: str) -> RespuestaIA:
        resultado = self.motor.responder_pregunta(servidor_id, nombre_servidor, pregunta)
        return RespuestaIA(resultado["texto"], fuentes=resultado["fuentes"], modo=resultado["modo"])

    async def sugerir_moderacion(self, servidor_id: str, nombre_servidor: str, mensaje: str, contexto: str = "") -> dict:
        return self.motor.sugerir_moderacion(mensaje, contexto)

    async def plan_constructor(self, descripcion: str, max_roles: int = 30, max_canales: int = 100) -> dict:
        return self.motor.plan_constructor(descripcion, max_roles, max_canales)

    async def resumir(self, servidor_id: str, nombre_servidor: str, mensajes: list[str]) -> str:
        return self.motor.resumir(mensajes)


def extraer_json(texto: str) -> str:
    """Extrae el primer objeto o array JSON balanceado de un texto."""
    inicio = texto.find("{")
    if inicio == -1:
        inicio = texto.find("[")
    if inicio == -1:
        raise ValueError("No se encontró JSON en la respuesta")
    abre = texto[inicio]
    cierra = "}" if abre == "{" else "]"
    profundidad = 0
    en_cadena = False
    escape = False
    for i in range(inicio, len(texto)):
        c = texto[i]
        if en_cadena:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                en_cadena = False
            continue
        if c == '"':
            en_cadena = True
        elif c == abre:
            profundidad += 1
        elif c == cierra:
            profundidad -= 1
            if profundidad == 0:
                return texto[inicio : i + 1]
    raise ValueError("JSON sin cerrar en la respuesta")


def plan_por_defecto(descripcion: str) -> dict:
    """Plan inicial sincrónico, útil antes de poder llamar al motor."""
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
                ],
            },
            {"nombre": "GENERAL", "canales": [{"nombre": "general", "tipo": "texto", "solo_lectura": False}]},
        ],
        "mensajes": [{"canal": "reglas", "contenido": "1. Respeto."}],
        "modulos": ["bienvenida", "tickets"],
        "tipo_detectado": "general",
    }
