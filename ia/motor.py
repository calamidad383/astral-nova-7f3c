"""Motor de IA propio y autocontenido (sin APIs externas).

Se "entrena" en tres sentidos, todos locales:
1. Índice TF-IDF construido a partir de la base de conocimiento de cada
   servidor (se recalcula al añadir documentos: `entrenar`).
2. Aprendizaje por retroalimentación: cada pulgar arriba/abajo y cada
   rechazo de moderación ajusta pesos persistidos (`aprender`).
3. Léxicos y plantillas propias para toxicidad, intenciones y planes.

Nada de este módulo necesita claves ni conexión a servicios de terceros.
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

from .rag import RAG, tokenizar


# ---------------------------------------------------------------- utilidades

def normalizar_agresivo(texto: str) -> str:
    """minúsculas, sin acentos, sin leetspeak, sin caracteres repetidos."""
    tabla = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i"})
    texto = unicodedata.normalize("NFKD", texto).translate(tabla)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"(.)\1{2,}", r"\1\1", texto)
    return texto.lower()


# ---------------------------------------------------------------- léxicos

# Léxico de toxicidad por gravedad (1 = leve, 3 = grave). Sin groserías
# explícitas de alto riesgo: se clasifican por categorías y patrones.
TOXICIDAD = {
    1: ["tonto", "tonta", "malo", "callate", "cállate", "noob", "basura", "molesto", "odio este"],
    2: ["idiota", "idiotа", "estupido", "estúpida", "imbecil", "inutil", "inútil", "burro", "payaso", "payasa", "mierda", "puta", "pendejo"],
    3: ["matar", "mates", "muere", "vete a morir", "te voy a matar", "amenaza", "violación", "violar"],
}

PATRONES_SCAM = [
    (r"nitro\s*(gratis|free)", "scam de Nitro"),
    (r"(regala|regalo|giveaway).*(nitro|steam)", "scam de regalos"),
    (r"(free\s*)?(robux|vbucks|cripto|crypto).*(gratis|free|gratis)", "scam de monedas/cripto"),
    (r"discord\.(gg|com)/[a-z0-9]{6,}", "invitación externa"),
    (r"(invierte|inversion|inversión).*(garantizado|100%|seguro)", "scam de inversión"),
    (r"steamcommunity\.(?!com)", "phishing de Steam"),
    (r"d1scord|discorcl|discrod", "suplantación de Discord"),
]

PALABRAS_INVITES = ("discord.gg/", "invite.gg", "dsc.gg")


# ---------------------------------------------------------------- planes del constructor

PLANTILLAS_COMUNIDAD = {
    "gaming": {
        "claves": ["gaming", "juego", "juegos", "clan", "esports", "valorant", "minecraft", "fortnite", "roblox"],
        "roles": [("Dueño de clan", "#EF4444", "moderador"), ("Jugador", "#5865F2", "miembro"), ("Espectador", "#9AA0B4", "miembro")],
        "categorias": [
            ("GENERAL", [("bienvenida", "texto", True), ("reglas", "texto", True), ("anuncios", "texto", True)]),
            ("JUEGOS", [("general", "texto", False), ("clips-y-momentos", "texto", False), ("busco-equipo", "texto", False), ("sala-de-juego", "voz", False)]),
            ("SOPORTE", [("tickets", "texto", False)]),
        ],
        "modulos": ["bienvenida", "tickets", "anti_spam", "niveles", "encuestas", "roles_botones"],
    },
    "academia": {
        "claves": ["academia", "curso", "cursos", "clase", "clases", "estudio", "estudiar", "ingles", "inglés", "aprender", "educativo", "escuela", "tutoria"],
        "roles": [("Profesor", "#F59E0B", "moderador"), ("Estudiante", "#5865F2", "miembro"), ("Ayudante", "#22C55E", "moderador")],
        "categorias": [
            ("INFORMACIÓN", [("bienvenida", "texto", True), ("reglas", "texto", True), ("horarios", "texto", True)]),
            ("CLASES", [("general", "texto", False), ("tareas", "texto", False), ("dudas", "texto", False), ("sala-de-practica", "voz", False)]),
            ("SOPORTE", [("tickets", "texto", False)]),
        ],
        "modulos": ["bienvenida", "tickets", "anti_spam", "pregunta", "encuestas", "recordatorios"],
    },
    "negocio": {
        "claves": ["tienda", "negocio", "venta", "vender", "clientes", "servicio", "productos", "compra"],
        "roles": [("Cliente VIP", "#F59E0B", "miembro"), ("Cliente", "#5865F2", "miembro"), ("Atención", "#22C55E", "moderador")],
        "categorias": [
            ("TIENDA", [("bienvenida", "texto", True), ("catalogo", "texto", True), ("ofertas", "texto", True)]),
            ("ATENCIÓN", [("dudas", "texto", False), ("tickets", "texto", False), ("sala-de-reunion", "voz", False)]),
        ],
        "modulos": ["bienvenida", "tickets", "anti_spam", "encuestas", "anuncios"],
    },
    "trading": {
        "claves": ["trading", "trader", "bolsa", "inversion", "inversión", "finanzas", "educacion financiera"],
        "roles": [("Mentor", "#F59E0B", "moderador"), ("Alumno Pro", "#22C55E", "miembro"), ("Alumno", "#5865F2", "miembro")],
        "categorias": [
            ("INFORMACIÓN", [("bienvenida", "texto", True), ("reglas", "texto", True), ("disclaimer-educativo", "texto", True)]),
            ("COMUNIDAD", [("general", "texto", False), ("dudas-educativas", "texto", False), ("biblioteca", "texto", False), ("sala-de-estudio", "voz", False)]),
            ("SOPORTE", [("tickets", "texto", False)]),
        ],
        "modulos": ["bienvenida", "tickets", "anti_spam", "pregunta", "niveles", "anuncios"],
    },
    "creador": {
        "claves": ["creador", "streamer", "twitch", "youtube", "contenido", "fans", "suscriptores"],
        "roles": [("Suscriptor VIP", "#7C5CFF", "miembro"), ("Fan", "#5865F2", "miembro"), ("Moderador de live", "#22C55E", "moderador")],
        "categorias": [
            ("CANAL", [("bienvenida", "texto", True), ("reglas", "texto", True), ("anuncios-de-directo", "texto", True)]),
            ("COMUNIDAD", [("general", "texto", False), ("fan-art", "texto", False), ("sugerencias", "texto", False), ("sala-del-directo", "voz", False)]),
        ],
        "modulos": ["bienvenida", "anti_spam", "niveles", "roles_botones", "anuncios"],
    },
}

PLANTILLA_GENERAL = {
    "roles": [("Moderador", "#F59E0B", "moderador"), ("Miembro", "#5865F2", "miembro")],
    "categorias": [
        ("INFORMACIÓN", [("bienvenida", "texto", True), ("reglas", "texto", True), ("anuncios", "texto", True)]),
        ("GENERAL", [("general", "texto", False), ("soporte", "texto", False)]),
    ],
    "modulos": ["bienvenida", "tickets", "anti_spam", "encuestas"],
}

REGLAS_BASE = (
    "Reglas del servidor:\n"
    "1. Respeto ante todo: no insultos ni acoso.\n"
    "2. Sin spam ni publicidad sin permiso.\n"
    "3. Contenido adecuado para todos los públicos.\n"
    "4. Sigue las indicaciones del staff."
)


# ---------------------------------------------------------------- intenciones del chat admin

INTENCIONES_ADMIN = [
    ("crear_canal", [r"crea.*canal", r"nuevo canal", r"crear.*#"]),
    ("crear_rol", [r"crea.*rol", r"nuevo rol"]),
    ("silenciar", [r"silencia", r"mutea", r"mute"]),
    ("expulsar", [r"expulsa", r"kick"]),
    ("banear", [r"banea", r"ban(?!de)"]),
    ("resumir", [r"resume", r"resumen"]),
    ("activar_modulo", [r"activa", r"enciende"]),
    ("desactivar_modulo", [r"desactiva", r"apaga"]),
    ("salud", [r"como va el servidor", r"salud del servidor", r"estado del servidor"]),
]


@dataclass
class Entrenamiento:
    documentos: int = 0
    terminos: int = 0
    version: int = 0


@dataclass
class MotorLocal:
    """Cerebro local entrenable. Persiste el aprendizaje en SQLite."""

    rag: RAG
    db_path: str
    umbral_respuesta: float = 0.35
    _idf: dict = field(default_factory=dict, repr=False)
    _doc_tokens: dict = field(default_factory=dict, repr=False)
    _pesos_aprendidos: dict = field(default_factory=dict, repr=False)

    # ------------------------------------------------ entrenamiento

    def entrenar(self, servidor_id: str | None = None) -> Entrenamiento:
        """Construye el índice TF-IDF y carga los pesos aprendidos."""
        documentos = self.rag.listar(servidor_id) if servidor_id else self.rag.listar_todos()
        self._doc_tokens = {}
        frecuencias: Counter = Counter()
        for doc in documentos:
            tokens = set(tokenizar(doc.titulo + " " + doc.contenido))
            self._doc_tokens[(doc.servidor_id, doc.id)] = tokens
            frecuencias.update(tokens)
        total_docs = max(len(documentos), 1)
        self._idf = {t: math.log((total_docs + 1) / (n + 1)) + 1.0 for t, n in frecuencias.items()}
        self._pesos_aprendidos = self._cargar_pesos()
        return Entrenamiento(documentos=len(documentos), terminos=len(self._idf))

    def _cargar_pesos(self) -> dict:
        con = sqlite3.connect(self.db_path)
        try:
            self._asegurar_tabla(con)
            filas = con.execute("SELECT servidor_id, id_doc, peso FROM ia_aprendizaje").fetchall()
            return {(s, d): p for s, d, p in filas}
        finally:
            con.close()

    @staticmethod
    def _asegurar_tabla(con: sqlite3.Connection) -> None:
        con.execute(
            "CREATE TABLE IF NOT EXISTS ia_aprendizaje (servidor_id TEXT, id_doc TEXT, peso REAL, PRIMARY KEY (servidor_id, id_doc))"
        )

    def aprender(self, servidor_id: str, id_doc: str, util: bool) -> float:
        """Refuerza o debilita un documento según feedback humano."""
        delta = 0.15 if util else -0.20
        clave = (servidor_id, id_doc)
        nuevo = max(-1.0, min(2.0, self._pesos_aprendidos.get(clave, 0.0) + delta))
        self._pesos_aprendidos[clave] = nuevo
        con = sqlite3.connect(self.db_path)
        try:
            self._asegurar_tabla(con)
            con.execute(
                "INSERT OR REPLACE INTO ia_aprendizaje (servidor_id, id_doc, peso) VALUES (?, ?, ?)",
                (servidor_id, id_doc, nuevo),
            )
            con.commit()
        finally:
            con.close()
        return nuevo

    # ------------------------------------------------ preguntas con citas

    def _puntuar_doc(self, servidor_id: str, id_doc: str, palabras: Counter) -> float:
        tokens = self._doc_tokens.get((servidor_id, id_doc))
        if not tokens:
            return 0.0
        puntaje = 0.0
        for p, n in palabras.items():
            if p in tokens:
                puntaje += n * self._idf.get(p, 1.0)
        return puntaje * (1.0 + max(0.0, self._pesos_aprendidos.get((servidor_id, id_doc), 0.0)))

    def responder_pregunta(self, servidor_id: str, nombre_servidor: str, pregunta: str) -> dict:
        self.entrenar(servidor_id)
        palabras = Counter(tokenizar(pregunta))
        if not palabras:
            return self._no_se()
        puntuados = sorted(
            ((self._puntuar_doc(servidor_id, doc.id, palabras), doc) for doc in self.rag.listar(servidor_id)),
            key=lambda x: x[0],
            reverse=True,
        )
        mejor_puntaje, mejor = puntuados[0] if puntuados else (0.0, None)
        if not mejor or mejor_puntaje < self.umbral_respuesta:
            return self._no_se()
        oraciones = self._mejores_oraciones(mejor.contenido, palabras, maximo=3)
        respuesta = " ".join(oraciones) if oraciones else mejor.contenido[:400]
        fuentes = [doc.id for p, doc in puntuados[:2] if p >= self.umbral_respuesta * 0.6]
        return {
            "texto": f"{respuesta}\n\nFuentes: {', '.join(dict.fromkeys([mejor.id] + fuentes))}",
            "fuentes": list(dict.fromkeys([mejor.id] + fuentes)),
            "modo": "local",
            "confianza": min(1.0, mejor_puntaje / (mejor_puntaje + 3)),
        }

    def _no_se(self) -> dict:
        return {
            "texto": "No tengo esa información en la base de conocimiento del servidor. Derivaré tu pregunta a un moderador.",
            "fuentes": [],
            "modo": "local",
            "confianza": 0.0,
        }

    @staticmethod
    def _mejores_oraciones(contenido: str, palabras: Counter, maximo: int = 3) -> list[str]:
        oraciones = [o.strip() for o in re.split(r"(?<=[.!?])\s+|\n+", contenido) if len(o.strip()) > 10]
        if not oraciones:
            return []
        puntuadas = []
        for i, oracion in enumerate(oraciones):
            tokens = tokenizar(oracion)
            puntaje = sum(palabras.get(t, 0) for t in tokens) / (len(tokens) ** 0.5 or 1)
            puntaje += max(0.0, 1.0 - i * 0.05)
            puntuadas.append((puntaje, i, oracion))
        puntuadas.sort(reverse=True)
        elegidas = sorted(i for _, i, _ in puntuadas[:maximo])
        return [oraciones[i] for i in elegidas]

    # ------------------------------------------------ moderación

    def sugerir_moderacion(self, mensaje: str, contexto: str = "") -> dict:
        texto = normalizar_agresivo(mensaje)
        gravedad = 0
        categorias = []
        for nivel, palabras in TOXICIDAD.items():
            for palabra in palabras:
                if re.search(rf"\b{re.escape(normalizar_agresivo(palabra))}\b", texto):
                    gravedad = max(gravedad, nivel)
                    categorias.append(palabra)
        for patron, nombre in PATRONES_SCAM:
            if re.search(patron, texto):
                gravedad = max(gravedad, 3)
                categorias.append(nombre)
        if any(inv in mensaje.lower() for inv in PALABRAS_INVITES):
            gravedad = max(gravedad, 2)
            categorias.append("publicidad no permitida")

        mayusculas = sum(1 for c in mensaje if c.isupper())
        if len(mensaje) > 20 and mayusculas / len(mensaje) > 0.7:
            gravedad = max(gravedad, 1)
            categorias.append("gritos (mayúsculas)")

        if gravedad == 0:
            return {"accion": "nada", "motivo": "Mensaje inofensivo", "confianza": 0.9}
        if gravedad == 1:
            return {"accion": "advertencia", "motivo": f"Tono inapropiado: {', '.join(categorias[:2])}", "confianza": 0.6}
        if gravedad == 2:
            return {"accion": "eliminar_mensaje", "motivo": f"Infracción leve-moderada: {', '.join(categorias[:2])}", "confianza": 0.75}
        return {"accion": "escalar", "motivo": f"Grave, decisión humana: {', '.join(categorias[:2])}", "confianza": 0.85}

    # ------------------------------------------------ chat de administración

    def clasificar_intencion(self, orden: str) -> tuple[str, dict]:
        texto = normalizar_agresivo(orden)
        for intencion, patrones in INTENCIONES_ADMIN:
            for patron in patrones:
                if re.search(patron, texto):
                    return intencion, self._extraer_parametros(intencion, orden)
        return "desconocida", {}

    @staticmethod
    def _extraer_parametros(intencion: str, orden: str) -> dict:
        parametros: dict = {}
        canal = re.search(r"#([a-z0-9\-_]+)", orden.lower())
        if canal:
            parametros["canal"] = canal.group(1)
        nombre = re.search(r"(?:llamad[oa]|nombre|llamado)\s+[\"']?([\w\- ]{2,30})", orden.lower())
        if nombre:
            parametros["nombre"] = nombre.group(1).strip()
        usuario = re.search(r"@(\w+)", orden)
        if usuario:
            parametros["usuario"] = usuario.group(1)
        return parametros

    # ------------------------------------------------ constructor de servidores

    def plan_constructor(self, descripcion: str, max_roles: int = 30, max_canales: int = 100) -> dict:
        texto = normalizar_agresivo(descripcion)
        tipo_elegido, mejor = "general", 0
        for tipo, datos in PLANTILLAS_COMUNIDAD.items():
            coincidencias = sum(1 for clave in datos["claves"] if clave in texto)
            if coincidencias > mejor:
                tipo_elegido, mejor = tipo, coincidencias
        plantilla = PLANTILLAS_COMUNIDAD.get(tipo_elegido, {"roles": PLANTILLA_GENERAL["roles"], "categorias": PLANTILLA_GENERAL["categorias"], "modulos": PLANTILLA_GENERAL["modulos"]})
        roles, categorias, modulos = plantilla["roles"], plantilla["categorias"], list(plantilla["modulos"])
        if "vip" in texto or "pago" in texto or "suscripcion" in texto or "suscripción" in texto:
            roles = list(roles) + [("VIP", "#7C5CFF", "miembro")]
            modulos.append("anuncios")
        temas = [t for t in tokenizar(descripcion) if len(t) > 3][:3]
        nombre = " ".join(temas) if temas else "la comunidad"
        plan = {
            "roles": [{"nombre": n, "color": c, "plantilla": p} for n, c, p in roles],
            "categorias": [
                {"nombre": cat, "canales": [{"nombre": cn, "tipo": tp, "solo_lectura": sl} for cn, tp, sl in canales]}
                for cat, canales in categorias
            ],
            "mensajes": [
                {"canal": "reglas", "contenido": REGLAS_BASE},
                {"canal": "bienvenida", "contenido": f"¡Bienvenido a {nombre}! Lee #reglas y preséntate en #general."},
            ],
            "modulos": sorted(set(modulos)),
            "tipo_detectado": tipo_elegido,
        }
        if len(plan["roles"]) > max_roles or sum(len(c["canales"]) + 1 for c in plan["categorias"]) > max_canales:
            plan = self.plan_constructor("general", max_roles, max_canales)
        return plan

    # ------------------------------------------------ resúmenes

    def resumir(self, mensajes: list[str], maximo: int = 6) -> str:
        if not mensajes:
            return "No hay mensajes para resumir."
        palabras = Counter(t for m in mensajes for t in tokenizar(m))
        puntuados = []
        for i, mensaje in enumerate(mensajes):
            tokens = tokenizar(mensaje)
            if len(tokens) < 3:
                continue
            puntaje = sum(palabras.get(t, 0) for t in tokens) / (len(tokens) ** 0.5)
            autor_oculto = re.sub(r"^\w{3}\S*", lambda m: m.group(0)[:3] + "***", mensaje, count=1)
            puntuados.append((puntaje, i, autor_oculto[:160]))
        if not puntuados:
            return "No hay mensajes suficientes para resumir."
        texto_por_indice = {i: t for _, i, t in puntuados}
        puntuados.sort(reverse=True)
        elegidas = sorted(i for _, i, _ in puntuados[:maximo])
        viñetas = [f"• {texto_por_indice[i]}" for i in elegidas]
        return "Resumen de actividad:\n" + "\n".join(viñetas)
