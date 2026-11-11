# Contribuir

¡Gracias por querer ayudar! Este proyecto se construye por fases (ver `ESTADO.md` y la hoja de ruta del README).

## Cómo contribuir

1. Abre un issue primero si el cambio es grande, para acordar el enfoque.
2. Crea una rama descriptiva desde `main`.
3. Haz cambios pequeños y enfocados, con pruebas cuando aplique.
4. Abre un pull request describiendo qué resuelve y cómo lo probaste.

## Reglas

- Nunca incluyas tokens, claves o datos reales de usuarios en el código, las pruebas o los issues.
- Python: sigue el estilo del código existente; las pruebas van en `tests/` y se ejecutan con `pytest`.
- Los módulos del bot son *cogs* independientes en `bot/cogs/`; no acoples módulos entre sí.
- Toda acción del bot debe ser reversible o registrada.
- La IA solo **sugiere** en moderación: un humano decide sanciones.

## Entorno de desarrollo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r bot/requirements.txt -r api/requirements.txt -r tests/requirements.txt
cp .env.example .env   # rellena lo que necesites para pruebas locales
pytest
```
