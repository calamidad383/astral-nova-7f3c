"""Base de conocimiento con búsqueda (RAG) y citas.

Fase 1: búsqueda por palabras clave con puntuación TF simple, sobre SQLite.
Fase 2: vectores y búsqueda semántica (misma interfaz).
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from dataclasses import dataclass

_STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y", "o", "a",
    "en", "que", "es", "del", "al", "por", "para", "con", "como", "su", "sus",
    "the", "of", "to", "and", "is", "in", "for", "on", "it", "this", "that",
}


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def tokenizar(texto: str) -> list[str]:
    palabras = re.findall(r"[a-z0-9]{2,}", normalizar(texto))
    return [p for p in palabras if p not in _STOPWORDS]


@dataclass
class Fragmento:
    id: str
    servidor_id: str
    titulo: str
    contenido: str


class RAG:
    """Base de conocimiento por servidor, con respuestas citadas."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._crear_tabla()

    def _conectar(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def _crear_tabla(self) -> None:
        with self._conectar() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS conocimiento (
                    id TEXT PRIMARY KEY,
                    servidor_id TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    contenido TEXT NOT NULL,
                    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def añadir(self, servidor_id: str, titulo: str, contenido: str, id_: str | None = None) -> str:
        id_ = id_ or f"{titulo.strip().lower().replace(' ', '-')[:40]}"
        with self._conectar() as con:
            con.execute(
                "INSERT OR REPLACE INTO conocimiento (id, servidor_id, titulo, contenido) VALUES (?, ?, ?, ?)",
                (id_, servidor_id, titulo, contenido),
            )
        return id_

    def eliminar(self, servidor_id: str, id_: str) -> bool:
        with self._conectar() as con:
            cur = con.execute(
                "DELETE FROM conocimiento WHERE servidor_id = ? AND id = ?",
                (servidor_id, id_),
            )
            return cur.rowcount > 0

    def listar(self, servidor_id: str) -> list[Fragmento]:
        with self._conectar() as con:
            filas = con.execute(
                "SELECT id, servidor_id, titulo, contenido FROM conocimiento WHERE servidor_id = ?",
                (servidor_id,),
            ).fetchall()
        return [Fragmento(**dict(fila)) for fila in filas]

    def buscar(self, servidor_id: str, pregunta: str, limite: int = 3) -> list[Fragmento]:
        palabras = set(tokenizar(pregunta))
        resultados: list[tuple[float, Fragmento]] = []
        for frag in self.listar(servidor_id):
            tokens = tokenizar(frag.titulo + " " + frag.contenido)
            if not tokens:
                continue
            frecuencia: dict[str, int] = {}
            for t in tokens:
                frecuencia[t] = frecuencia.get(t, 0) + 1
            puntaje = 0.0
            for p in palabras:
                if p in frecuencia:
                    puntaje += 1 + min(frecuencia[p], 5) / 10
                    if p in tokenizar(frag.titulo):
                        puntaje += 0.5
            if puntaje > 0:
                resultados.append((puntaje, frag))
        resultados.sort(key=lambda x: x[0], reverse=True)
        return [frag for _, frag in resultados[:limite]]

    def contexto(self, servidor_id: str, pregunta: str, limite: int = 3) -> tuple[str, list[str]]:
        """Devuelve (texto_de_contexto, ids_de_fuentes) para el prompt."""
        fragmentos = self.buscar(servidor_id, pregunta, limite)
        if not fragmentos:
            return "", []
        partes = [f"[{f.id}] {f.titulo}\n{f.contenido}" for f in fragmentos]
        return "\n\n".join(partes), [f.id for f in fragmentos]
