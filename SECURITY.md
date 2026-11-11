# Seguridad

## Reportar una vulnerabilidad

**No abras un issue público para vulnerabilidades.** Usa el formulario de soporte de la app o contacta al mantenedor directamente. Respondemos en un plazo de 72 horas y trabajamos en una corrección antes de cualquier divulgación pública.

## Buenas prácticas de este proyecto

- Los tokens y claves (Discord, Gemini, PayPal) viven **solo** en variables de entorno del servidor, nunca en el código ni en el repositorio.
- La app instalada **nunca** contiene claves: habla con la API, y la API con el bot.
- Los webhooks de PayPal se **verifican por firma** antes de actuar.
- La IA **nunca** ejecuta acciones sensibles sin aprobación humana, y ningún rol creado por la IA tiene el permiso de Administrador.
- Todas las acciones del constructor quedan registradas y se pueden deshacer.
- Lanzamientos con hash SHA-256 publicados en GitHub Releases.

## Para quien autoaloja

- Usa `docker/` y no expongas la base de datos ni Redis a internet.
- Cambia `API_SECRET_KEY` por una clave larga y aleatoria.
- Mantén 2FA activada en la cuenta de Discord del bot y del servidor.
