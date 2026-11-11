"""Pruebas del constructor y del RAG (sin Discord ni red)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot import constructor  # noqa: E402
from ia.cerebro import extraer_json, plan_por_defecto  # noqa: E402
from ia.rag import RAG  # noqa: E402


# ---------------------------------------------------------------- constructor

PLAN_VALIDO = {
    "roles": [
        {"nombre": "Profesor", "color": "#F59E0B", "plantilla": "moderador"},
        {"nombre": "Estudiante", "color": "#5865F2", "plantilla": "miembro"},
    ],
    "categorias": [
        {
            "nombre": "INFORMACIÓN",
            "canales": [
                {"nombre": "Bienvenida", "tipo": "texto", "solo_lectura": True},
                {"nombre": "Reglas", "tipo": "texto", "solo_lectura": True},
            ],
        },
        {"nombre": "CLASES", "canales": [{"nombre": "General", "tipo": "texto"}]},
    ],
    "mensajes": [{"canal": "Reglas", "contenido": "1. Respeto."}],
    "modulos": ["bienvenida", "tickets"],
}


def test_validar_plan_valido():
    constructor.validar(PLAN_VALIDO)


def test_validar_rechaza_demasiados_roles():
    plan = {"roles": [{"nombre": f"r{i}", "color": "#000000", "plantilla": "miembro"} for i in range(31)]}
    with pytest.raises(constructor.PlanInvalido):
        constructor.validar(plan)


def test_validar_rechaza_plantilla_desconocida():
    plan = {"roles": [{"nombre": "X", "color": "#000000", "plantilla": "admin"}]}
    with pytest.raises(constructor.PlanInvalido):
        constructor.validar(plan)


def test_validar_rechaza_demasiados_canales():
    categoria = {"nombre": "C", "canales": [{"nombre": f"c{i}", "tipo": "texto"} for i in range(60)]}
    plan = {"categorias": [categoria, dict(categoria)]}
    with pytest.raises(constructor.PlanInvalido):
        constructor.validar(plan)


def test_validar_rechaza_tipo_canal_desconocido():
    plan = {"categorias": [{"nombre": "C", "canales": [{"nombre": "x", "tipo": "foro"}]}]}
    with pytest.raises(constructor.PlanInvalido):
        constructor.validar(plan)


def test_normalizar_nombre():
    assert constructor.normalizar_nombre("Sala de Práctica") == "sala-de-practica"
    assert constructor.normalizar_nombre("Información") == "informacion"


# ---------------------------------------------------------------- plan por defecto

def test_plan_por_defecto_es_valido():
    plan = plan_por_defecto("comunidad de inglés")
    constructor.validar(plan)
    assert plan["roles"] and plan["categorias"] and plan["modulos"]


def test_extraer_json_con_markdown():
    texto = '```json\n{"a": 1}\n```'
    assert extraer_json(texto) == '{"a": 1}'


def test_extraer_json_con_texto_alrededor():
    assert extraer_json('Aquí tienes:\n{"a": {"b": 2}}\n¿algo más?') == '{"a": {"b": 2}}'


# ---------------------------------------------------------------- RAG

@pytest.fixture
def rag(tmp_path):
    return RAG(str(tmp_path / "test.db"))


def test_rag_añadir_y_buscar_con_citas(rag):
    rag.añadir("srv1", "FAQ de pagos", "El plan Pro cuesta 8 dólares al mes y se paga con PayPal.")
    rag.añadir("srv1", "Reglas", "Se prohíbe el spam y los enlaces de publicidad.")
    fragmentos = rag.buscar("srv1", "¿cuánto cuesta el plan pro y cómo pago?")
    assert fragmentos, "Debe encontrar el documento de pagos"
    assert "pagos" in fragmentos[0].id


def test_rag_no_cruza_servidores(rag):
    rag.añadir("srv1", "FAQ", "contenido secreto del srv1")
    assert rag.buscar("srv2", "contenido secreto") == []


def test_rag_contexto_vacio(rag):
    texto, fuentes = rag.contexto("srv1", "pregunta sin documentos")
    assert texto == "" and fuentes == []


def test_rag_eliminar(rag):
    rag.añadir("srv1", "FAQ", "contenido")
    assert rag.eliminar("srv1", "faq") is True
    assert rag.eliminar("srv1", "faq") is False


# ---------------------------------------------------------------- evaluaciones estructurales

def test_acciones_de_moderacion_permitidas():
    from ia.evaluaciones import ACCIONES_PERMITIDAS, ACCIONES_PROHIBIDAS

    assert ACCIONES_PROHIBIDAS.isdisjoint(ACCIONES_PERMITIDAS)
