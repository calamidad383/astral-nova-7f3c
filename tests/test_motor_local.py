"""Pruebas del motor de IA local y del sistema de seguridad (sin red ni Discord)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.seguridad import Seguridad  # noqa: E402
from ia.motor import MotorLocal  # noqa: E402
from ia.rag import RAG  # noqa: E402


SERVIDOR = "srv-test"


def _motor(tmp_path) -> MotorLocal:
    db = str(tmp_path / "motor.db")
    rag = RAG(db)
    rag.añadir(SERVIDOR, "FAQ de pagos", "Las suscripciones se pagan con PayPal. El plan pro cuesta 8 dolares al mes.")
    rag.añadir(SERVIDOR, "Reglas", "No se permite spam ni publicidad externa. Respeta a los demas miembros.")
    return MotorLocal(rag=rag, db_path=db)


# ---------------------------------------------------------------- preguntas

def test_responde_con_cita(tmp_path):
    motor = _motor(tmp_path)
    r = motor.responder_pregunta(SERVIDOR, "Test", "¿Cuánto cuesta el plan pro?")
    assert r["fuentes"], "debe citar al menos una fuente"
    assert r["modo"] == "local"
    assert "paypal" in r["texto"].lower() or "8" in r["texto"]


def test_no_sabe_cuando_no_hay_coincidencia(tmp_path):
    motor = _motor(tmp_path)
    r = motor.responder_pregunta(SERVIDOR, "Test", "¿Cuál es la masa del agujero negro Sagitario A?")
    assert r["fuentes"] == []
    assert r["confianza"] == 0.0


def test_entrenamiento_devuelve_cifras(tmp_path):
    motor = _motor(tmp_path)
    e = motor.entrenar(SERVIDOR)
    assert e.documentos == 2
    assert e.terminos > 0


def test_aprender_persiste_peso(tmp_path):
    motor = _motor(tmp_path)
    docs = motor.rag.listar(SERVIDOR)
    peso = motor.aprender(SERVIDOR, docs[0].id, util=True)
    assert peso > 0
    motor2 = MotorLocal(rag=motor.rag, db_path=motor.db_path)
    e2 = motor2.entrenar(SERVIDOR)
    assert e2.documentos == 2
    assert motor2._pesos_aprendidos[(SERVIDOR, docs[0].id)] == peso


# ---------------------------------------------------------------- moderación

def test_moderacion_scam_nitro_escalada(tmp_path):
    motor = _motor(tmp_path)
    r = motor.sugerir_moderacion("¡GANA NITRO GRATIS ahora! discord.gg/premium123")
    assert r["accion"] == "escalar"
    assert r["confianza"] >= 0.8


def test_moderacion_mensaje_inofensivo(tmp_path):
    motor = _motor(tmp_path)
    r = motor.sugerir_moderacion("Hola, ¿cómo va todo hoy? Me encanta este servidor.")
    assert r["accion"] == "nada"


def test_moderacion_insulto_leve(tmp_path):
    motor = _motor(tmp_path)
    r = motor.sugerir_moderacion("eres un idiota")
    assert r["accion"] in {"eliminar_mensaje", "escalar"}


def test_moderacion_invitacion_externa(tmp_path):
    motor = _motor(tmp_path)
    r = motor.sugerir_moderacion("únanse a mi servidor discord.gg/otroservidor")
    assert r["accion"] in {"eliminar_mensaje", "escalar"}


# ---------------------------------------------------------------- constructor

def test_plan_constructor_gaming(tmp_path):
    motor = _motor(tmp_path)
    plan = motor.plan_constructor("Servidor de gaming para mi clan de Valorant")
    assert plan["tipo_detectado"] == "gaming"
    assert any(c["nombre"] == "JUEGOS" for c in plan["categorias"])


def test_plan_constructor_academia(tmp_path):
    motor = _motor(tmp_path)
    plan = motor.plan_constructor("Academia de inglés con clases y tareas")
    assert plan["tipo_detectado"] == "academia"


def test_plan_constructor_general_y_valido(tmp_path):
    from bot import constructor

    motor = _motor(tmp_path)
    plan = motor.plan_constructor("una comunidad cualquiera")
    constructor.validar(plan)
    assert plan["tipo_detectado"] == "general"


def test_plan_constructor_vip_extra(tmp_path):
    motor = _motor(tmp_path)
    plan = motor.plan_constructor("tienda con suscripción VIP de pago")
    assert any(r["nombre"] == "VIP" for r in plan["roles"])


# ---------------------------------------------------------------- resúmenes

def test_resumen_extractivo(tmp_path):
    motor = _motor(tmp_path)
    mensajes = [
        "ana: propongo un evento el viernes por la tarde",
        "luis: me parece bien el viernes, aviso en anuncios",
        "ana: perfecto, preparo el canal del evento",
        "x",
        "y",
    ]
    texto = motor.resumir(mensajes)
    assert texto.startswith("Resumen de actividad:")
    assert "•" in texto


def test_resumen_vacio(tmp_path):
    motor = _motor(tmp_path)
    assert "No hay mensajes" in motor.resumir([])


# ---------------------------------------------------------------- seguridad

def test_ban_permanente_tras_5_intentos(tmp_path):
    seg = Seguridad(str(tmp_path / "seg.db"))
    baneada = False
    for _ in range(5):
        baneada = seg.registrar_intento_fallido("10.0.0.1")
    assert baneada
    assert seg.esta_baneada("10.0.0.1")
    seg.desbanear("10.0.0.1")
    assert not seg.esta_baneada("10.0.0.1")


def test_intentos_reinician_con_ban(tmp_path):
    seg = Seguridad(str(tmp_path / "seg.db"))
    for _ in range(4):
        seg.registrar_intento_fallido("10.0.0.2")
    assert not seg.esta_baneada("10.0.0.2")
    seg.registrar_evento("prueba", "10.0.0.2", "detalle")
    assert any(e["tipo"] == "prueba" for e in seg.eventos())
