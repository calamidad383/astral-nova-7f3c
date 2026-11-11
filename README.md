# Plataforma IA para Discord — Guía v3 (versión masiva)

> Esta guía reemplaza a la v1 y a la v2. Describe una **plataforma completa**: una app que se descarga e instala en cada sistema, se conecta al Discord del usuario y, con ayuda de la IA, **crea y administra todo el servidor**. Incluye cómo se ve cada pantalla, el catálogo completo de módulos (todo lo que hacen los bots populares y más), la parte de IA, el cobro con PayPal, cómo compilar para cada plataforma y cómo darle fama. Está escrita para dársela a ChatGPT y construirla por fases.

---

## 0. Qué se añadió respecto a la v2

1. **Constructor de servidores con IA:** el usuario describe lo que quiere ("servidor para mi comunidad de trading educativo") y el sistema crea roles, categorías, canales, permisos, reglas, mensajes de bienvenida y tickets, con vista previa y botón de deshacer.
2. **Catálogo de más de 40 módulos** que reemplazan a los bots más usados: moderación, anti-raid, tickets, niveles, sorteos, encuestas, roles por reacción, registros, música (solo con fuentes legales), economía virtual, minijuegos, trivia, cumpleaños, recordatorios, comandos personalizados, notificaciones de Twitch/YouTube/Reddit, canales de voz temporales, contadores, sugerencias, solicitudes de staff, traducción, copias de seguridad y más.
3. **Módulos de IA de las ideas anteriores:** recepcionista con IA que agenda citas, tutor y coach con IA, creador de CV y cartas, generador de páginas web, clips de video y publicador en redes sociales (estos últimos, en fases avanzadas).
4. **Cómo se ve la app:** sistema de diseño completo (colores, tipografía, animaciones), navegación para móvil y escritorio, y descripción detallada de más de 30 pantallas, con esquemas.
5. **La parte de IA explicada de verdad:** capas del "cerebro" (instrucciones, base de conocimiento, memoria, herramientas, evaluación y límites de seguridad). Incluye una aclaración importante sobre "entrenar desde cero".
6. **Flujo completo del usuario:** descargar → instalar → iniciar sesión con Discord → añadir el bot → crear el servidor con IA.
7. **Aclaración de dónde corre el bot** y cómo se reparten las tareas entre la app y el servidor.
8. **Advertencias legales y técnicas** que cambian el plan (música, apuestas, trading, límites de Discord, tiendas de apps).
9. **Hoja de ruta por fases** para que construir algo tan grande no se quede a medias.
10. **Instrucciones ampliadas para ChatGPT** y lo que necesita conectar. Es la última sección, como pediste.

---

## 1. Visión

**Producto:** una app que convierte a la IA en el "administrador" de un servidor de Discord.

**Promesa al usuario:** "Descarga la app, conéctala a tu Discord, dile qué comunidad quieres y la IA monta y administra todo el servidor".

**Cliente ideal:** dueños de comunidades que ya generan dinero (cursos, trading educativo, gaming, creadores, academias, negocios con comunidad) y personas que quieren un servidor profesional sin saber configurarlo.

**Modelo de negocio:** código abierto en GitHub (fama y confianza) + planes de pago alojados por ti (comodidad, IA, soporte). Cobro con PayPal.

---

## 2. Aclaraciones importantes (lee esto antes de construir)

### 2.1 "Entrenar la IA desde cero" no es realista ni necesario
Entrenar un modelo de lenguaje desde cero cuesta millones de dólares, enormes cantidades de datos y servidores especializados. Ni ChatGPT ni nadie puede hacerlo desde un teléfono. Lo que sí se hace, y funciona muy bien:
- **Usar un modelo ya entrenado** (Gemini por API) como motor.
- **Darle instrucciones especializadas** (prompts de sistema) para cada tarea: moderar, atender, crear servidores.
- **Darle conocimiento propio** de cada servidor (base de conocimiento con búsqueda, llamada RAG).
- **Darle memoria** por servidor y por usuario.
- **Darle herramientas**: funciones que pueden crear canales, asignar roles, abrir tickets, etc.
- **Evaluarlo** con una lista de pruebas para que no se degrade.
- **Más adelante (opcional):** ajustar un modelo pequeño abierto con los datos reales de tus clientes, si de verdad hace falta.
Esto da el 95% del resultado por una fracción del costo.

### 2.2 Dónde corre el bot
Un bot de Discord **no corre dentro de la app instalada**. Corre en un servidor que está encendido 24/7. La app instalada es el **panel de control** que habla con ese servidor. Hay tres formas de tenerlo:
1. **Alojado por ti (nube):** el usuario solo descarga la app y todo funciona. Es la opción de pago.
2. **Autoalojado:** el usuario descarga el código abierto y lo corre en su propio servidor o en un Docker. Es la opción gratuita para técnicos.
3. **Modo local en escritorio (experimental):** el bot corre dentro de la app de Windows/Mac/Linux, pero solo funciona mientras la app esté abierta.

### 2.3 "Todos los sistemas del mundo"
Se puede cubrir: **Android, iPhone/iPad, Windows, macOS, Linux, ChromeOS y navegador web (instalable como app)**. Una versión para cada modelo de teléfono o computador no existe: se compila una por **sistema** y funciona en todos los modelos. Detalles en la sección 11.

### 2.4 Cosas que NO se deben incluir (o se incluyen de otra forma)
- **Música de YouTube y Spotify:** reproducir audio de esas plataformas con un bot viola sus términos y fue lo que obligó a cerrar bots famosos como Groovy y Rythm. El módulo de música se hace solo con **fuentes con licencia** (archivos propios del servidor, plataformas que lo permitan, música libre de derechos).
- **Apuestas con dinero real:** Discord las prohíbe. La economía del bot es **solo con monedas virtuales**.
- **Bots de trading y cripto:** no se incluyen. Implican riesgo legal y de pérdida de dinero para los clientes.
- **Mensajes masivos a los miembros (spam por DM):** causan bloqueo del bot.
- **Guardar datos de tarjetas:** nunca. PayPal se encarga.

### 2.5 ¿Se puede conectar ChatGPT a GitHub para que "lo conecte todo"?
ChatGPT tiene conectores que, si tu plan los ofrece, le permiten leer y escribir en tus repositorios **cuando tú lo autorizas**. Nadie puede conectarse a tu cuenta de GitHub sin tu permiso, y hay pasos que solo tú puedes hacer (crear el bot en Discord, las claves de PayPal, la cuenta de Apple). La sección 17 lo detalla.

---

## 3. Arquitectura general

```
        ┌──────────────── Usuarios del servidor ────────────────┐
        │                                                        │
        ▼                                                        │
   [ Discord ] ◄──────── Bot (Python, discord.py, módulos) ──────┤
                                   │                              │
 Dueño ──► [ App: Android · iOS · Windows · macOS · Linux · Web ] │
                      │                                           │
                      ▼                                           │
               [ API (FastAPI) ] ◄────────────────────────────────┘
                 │   │    │    │
                 │   │    │    └──► PayPal (pagos y webhooks)
                 │   │    └───────► Base de datos (SQLite → PostgreSQL)
                 │   └────────────► Cerebro IA (Gemini + RAG + memoria)
                 └────────────────► Cola de tareas (para trabajos largos)
```

**Reglas de oro:**
- La app **nunca** contiene claves ni el token del bot.
- Todo lo sensible (token de Discord, claves de Gemini y de PayPal) vive en variables de entorno del servidor.
- Los trabajos pesados (resúmenes grandes, video) van a una cola de tareas, no bloquean al bot.

---

## 4. Flujo completo del usuario

1. **Descarga** la app desde la sección de descargas de tu repositorio en GitHub (APK, instalador de Windows, `.dmg`, etc.) o abre la versión web.
2. **Instala** y abre la app. Ve 3 pantallas de bienvenida.
3. **Inicia sesión con Discord** (OAuth2): la app solo ve su identidad y los servidores que administra.
4. **Elige un servidor** (o crea uno nuevo en Discord y vuelve).
5. Toca **"Añadir el bot"**. Se abre Discord con la invitación y los permisos mínimos. Acepta.
6. La app detecta que el bot ya está dentro y pasa al **asistente de creación**.
7. El usuario **le cuenta a la IA qué comunidad quiere** (por texto o por voz).
8. La IA propone un **plan** (roles, canales, reglas, bienvenida, tickets, módulos activados).
9. El usuario ve una **vista previa visual**, edita lo que quiera y toca **"Aplicar"**.
10. El bot **crea todo el servidor**, con un registro de lo que hizo y un botón **"Deshacer"**.
11. Desde ahí el usuario administra todo desde la app: módulos, IA, analíticas, plan y pagos.

---

## 5. Cómo se ve la aplicación

### 5.1 Sistema de diseño
- **Estilo:** moderno, limpio, tipo "panel de control premium". Tema **oscuro por defecto**, tema claro opcional.
- **Colores (ejemplo):**
  - Fondo: `#0B0D12` (oscuro) / `#F6F7FB` (claro)
  - Superficie de tarjetas: `#141824` / `#FFFFFF`
  - Color principal (acciones): `#5865F2` (azul-violeta, cercano a Discord)
  - Acento IA: degradado `#7C5CFF → #22D3EE`
  - Éxito `#22C55E`, Aviso `#F59E0B`, Error `#EF4444`
- **Tipografía:** Inter (o la fuente del sistema). Títulos 24–32 px en negrita, texto 14–16 px.
- **Espaciado:** cuadrícula de 8 px. Tarjetas con esquinas de 16 px y sombra suave.
- **Animaciones:** transiciones de 200–300 ms, esqueletos de carga (en lugar de ruedas girando), micro-animaciones al aplicar cambios, efecto "escribiendo" cuando la IA responde.
- **Iconos:** un único conjunto de iconos de línea en toda la app.
- **Accesibilidad:** contraste alto, textos escalables, navegación por teclado en escritorio, etiquetas para lectores de pantalla.
- **Idiomas:** español e inglés al inicio; el resto se añade después.

### 5.2 Navegación
- **Móvil:** barra inferior con 5 pestañas: **Inicio · Servidor · IA · Módulos · Cuenta**.
- **Escritorio y web:** barra lateral izquierda con el selector de servidor arriba, secciones agrupadas, y una barra superior con búsqueda, notificaciones y perfil.
- **Atajo universal:** botón flotante **"Pregúntale a la IA"** en todas las pantallas.

### 5.3 Pantallas (lista completa)

**Entrada**
1. **Splash:** logo animado y degradado de fondo.
2. **Bienvenida (3 pasos):** qué hace la plataforma, ejemplos de servidores, privacidad.
3. **Inicio de sesión con Discord:** un solo botón grande + enlace a términos y privacidad.
4. **Selector de servidor:** tarjetas con icono, nombre, número de miembros y estado del bot.
5. **Añadir el bot:** explica los permisos pedidos uno por uno y por qué, con botón a Discord.

**Creación con IA**
6. **Asistente de creación (chat):** conversación con la IA; chips de ejemplo ("Comunidad de gaming", "Academia online", "Tienda").
7. **Plan propuesto:** resumen con roles, categorías, canales y módulos activados.
8. **Vista previa del servidor:** se ve como el árbol de canales de Discord, editable con arrastrar y soltar.
9. **Aplicando:** barra de progreso con cada paso ("Creando roles… 4/12").
10. **Resultado:** resumen y botón **"Deshacer todo"** (disponible por un tiempo).

**Panel**
11. **Inicio / Dashboard:** tarjetas de miembros, actividad, tickets abiertos, preguntas respondidas por la IA, estado del bot, y "Sugerencias de la IA" (por ejemplo, "Tu canal #ayuda recibe muchas preguntas sobre pagos: crea una FAQ").
12. **Salud del servidor:** puntuación de 0 a 100 con recomendaciones.
13. **Actividad en vivo:** línea de tiempo de eventos.

**Servidor**
14. **Estructura:** árbol de categorías y canales, roles y permisos.
15. **Roles y permisos:** matriz visual de permisos por rol, con plantillas seguras.
16. **Reglas y verificación:** editor de reglas, verificación de nuevos miembros (botón o captcha).
17. **Bienvenida y despedida:** editor con vista previa de mensajes e imágenes.
18. **Copias de seguridad:** lista de copias, restaurar, programar.

**Módulos**
19. **Tienda de módulos:** tarjetas por categoría (Moderación, Comunidad, Diversión, IA, Negocio), con interruptor para activar.
20. **Configuración de módulo:** pantalla propia para cada módulo (ver sección 7).
21. **Moderación:** casos, advertencias, historial por usuario, cola de revisión de la IA.
22. **Tickets:** bandeja con estados, prioridades y transcripciones.
23. **Niveles y recompensas:** curva de experiencia, roles por nivel, tabla de clasificación.
24. **Economía y minijuegos:** monedas virtuales, tienda, eventos.
25. **Sorteos y encuestas:** creador visual y calendario.
26. **Anuncios programados:** calendario con vista semanal.
27. **Notificaciones externas:** conectar Twitch, YouTube y Reddit.

**IA**
28. **Base de conocimiento:** documentos, preguntas frecuentes, preguntas que la IA no supo responder.
29. **Personalidad del bot:** nombre, tono (amigable, formal, divertido), idioma, límites.
30. **Chat con la IA administradora:** "Crea un canal de eventos solo para VIP", "Resume lo que pasó hoy".
31. **Resúmenes y reportes:** diarios y semanales, exportables.
32. **Pruebas de la IA:** laboratorio para probar respuestas antes de activarlas.

**Analíticas**
33. **Analíticas:** crecimiento, retención, horas activas, canales más usados, preguntas frecuentes, comparativas por semana.

**Cuenta**
34. **Plan y facturación:** plan actual, uso del mes, botón "Mejorar plan", historial de pagos, cancelar.
35. **Equipo:** invitar moderadores al panel con permisos limitados.
36. **Notificaciones:** centro de avisos y preferencias.
37. **Configuración:** idioma, tema, seguridad, exportar y eliminar mis datos.
38. **Ayuda y comunidad:** guías, enlace al repositorio, formulario de soporte, estado del servicio.

### 5.4 Esquemas de las pantallas clave

**Dashboard (escritorio)**
```
┌───────────────┬───────────────────────────────────────────────┐
│ ◉ Mi Servidor │  Inicio                         🔍  🔔  (perfil)│
│  ▸ Inicio     ├───────────────────────────────────────────────┤
│  ▸ Servidor   │ [Miembros 1,240 ↑5%] [Tickets 7] [IA 312 resp.]│
│  ▸ Módulos    │ [Salud del servidor 86/100 ████████░░]         │
│  ▸ IA         ├───────────────────────────────────────────────┤
│  ▸ Analíticas │ Actividad (7 días)        Sugerencias de la IA │
│  ▸ Plan       │ ▂▃▅▆▇▅▆                   • Crear FAQ de pagos │
│               │                           • Activar anti-raid  │
└───────────────┴───────────────────────────────────────────────┘
```

**Asistente de creación (móvil)**
```
┌─────────────────────────┐
│ ← Crear mi servidor     │
│                         │
│ 🤖 ¿Qué comunidad       │
│ quieres crear?          │
│                         │
│ [Gaming] [Academia]     │
│ [Tienda] [Creador]      │
│                         │
│            Quiero una   │
│            comunidad de │
│            inglés  ➤    │
│ ┌───────────────────┐   │
│ │ Escribe o habla 🎤│   │
│ └───────────────────┘   │
└─────────────────────────┘
```

**Vista previa del servidor**
```
 📁 INFORMACIÓN            👥 Roles
   # bienvenida              ● Dueño
   # reglas                  ● Profesor
   # anuncios                ● Estudiante
 📁 CLASES                   ● Moderador
   # general
   # tareas           [ Editar ]  [ Aplicar ]
   🔊 Sala de práctica
 📁 SOPORTE
   # tickets
```

**Tienda de módulos**
```
 Moderación ▸  [Anti-spam ●] [Anti-raid ○] [Registros ●]
 Comunidad  ▸  [Niveles ○]  [Sorteos ●]   [Encuestas ○]
 IA         ▸  [Asistente ●] [Resúmenes ○] [Tutor ○]
 Negocio    ▸  [Tickets ●]  [Citas ○]     [Solicitudes ○]
```

### 5.5 Estados y detalles de calidad
Cada pantalla debe tener: estado de carga (esqueleto), estado vacío con ilustración y botón de acción, estado de error con "Reintentar", modo sin conexión con aviso, y confirmaciones antes de acciones destructivas.

---

## 6. Constructor de servidores con IA

### 6.1 Cómo funciona
1. El usuario describe la comunidad (texto o voz).
2. La IA pregunta lo que falta (tamaño, idioma, tono, si habrá pagos o VIP).
3. La IA genera un **plan en formato JSON** (roles, categorías, canales, mensajes, módulos).
4. El sistema **valida el plan** contra los límites de Discord y las reglas de seguridad.
5. La app muestra la **vista previa**. El usuario edita y aprueba.
6. El bot **aplica el plan** paso a paso y guarda un registro para poder deshacerlo.

### 6.2 Reglas de seguridad del constructor
- La IA **nunca** ejecuta nada sin aprobación del usuario.
- Los permisos salen de **plantillas fijas** (Miembro, Moderador, Admin). La IA solo elige cuál asignar, no inventa permisos.
- **Nunca** se asigna el permiso de Administrador a un rol creado por la IA.
- Límites de Discord a respetar: hasta **500 canales** y **250 roles** por servidor. El sistema usa topes mucho menores por seguridad.
- Pausas entre acciones para respetar los límites de la API de Discord.
- Toda acción queda registrada con su identificador, para poder **deshacer**.
- Si el servidor ya tiene contenido, el constructor **añade**, no borra, salvo que el usuario lo pida expresamente y confirme.

### 6.3 Formato del plan

```json
{
  "roles": [
    {"nombre": "Profesor", "color": "#F59E0B", "plantilla": "moderador"},
    {"nombre": "Estudiante", "color": "#5865F2", "plantilla": "miembro"}
  ],
  "categorias": [
    {
      "nombre": "INFORMACIÓN",
      "canales": [
        {"nombre": "bienvenida", "tipo": "texto", "solo_lectura": true},
        {"nombre": "reglas", "tipo": "texto", "solo_lectura": true}
      ]
    },
    {
      "nombre": "CLASES",
      "canales": [
        {"nombre": "general", "tipo": "texto"},
        {"nombre": "sala-de-practica", "tipo": "voz"}
      ]
    }
  ],
  "mensajes": [
    {"canal": "reglas", "contenido": "1. Respeto ante todo..."}
  ],
  "modulos": ["bienvenida", "tickets", "anti_spam", "niveles"]
}
```

### 6.4 Código base: validar y aplicar el plan

```python
import asyncio
import discord

MAX_ROLES = 30
MAX_CANALES = 100
PLANTILLAS = {
    "miembro": discord.Permissions(view_channel=True, send_messages=True,
                                   read_message_history=True, connect=True, speak=True),
    "moderador": discord.Permissions(view_channel=True, send_messages=True,
                                     read_message_history=True, manage_messages=True,
                                     kick_members=True, moderate_members=True),
}


def validar(plan: dict) -> None:
    if len(plan.get("roles", [])) > MAX_ROLES:
        raise ValueError("Demasiados roles")
    total = sum(len(c["canales"]) + 1 for c in plan.get("categorias", []))
    if total > MAX_CANALES:
        raise ValueError("Demasiados canales")
    for r in plan.get("roles", []):
        if r["plantilla"] not in PLANTILLAS:
            raise ValueError(f"Plantilla desconocida: {r['plantilla']}")


async def aplicar(guild: discord.Guild, plan: dict, registro: list) -> None:
    roles = {}
    for r in plan.get("roles", []):
        rol = await guild.create_role(
            name=r["nombre"],
            colour=discord.Colour.from_str(r["color"]),
            permissions=PLANTILLAS[r["plantilla"]],
            reason="Constructor IA",
        )
        roles[r["nombre"]] = rol
        registro.append(("rol", rol.id))
        await asyncio.sleep(1)

    canales = {}
    for cat in plan.get("categorias", []):
        categoria = await guild.create_category(cat["nombre"], reason="Constructor IA")
        registro.append(("categoria", categoria.id))
        for c in cat["canales"]:
            overwrites = {}
            if c.get("solo_lectura"):
                overwrites[guild.default_role] = discord.PermissionOverwrite(send_messages=False)
            if c["tipo"] == "voz":
                canal = await guild.create_voice_channel(
                    c["nombre"], category=categoria, overwrites=overwrites)
            else:
                canal = await guild.create_text_channel(
                    c["nombre"], category=categoria, overwrites=overwrites)
            canales[c["nombre"]] = canal
            registro.append(("canal", canal.id))
            await asyncio.sleep(1)

    for m in plan.get("mensajes", []):
        canal = canales.get(m["canal"])
        if canal:
            await canal.send(m["contenido"][:1900])


async def deshacer(guild: discord.Guild, registro: list) -> None:
    for tipo, id_ in reversed(registro):
        objeto = guild.get_role(id_) if tipo == "rol" else guild.get_channel(id_)
        if objeto:
            await objeto.delete(reason="Deshacer constructor IA")
            await asyncio.sleep(1)
```

El bot necesita los permisos **Gestionar roles** y **Gestionar canales** (no Administrador) para esto.

---

## 7. Catálogo de módulos del bot

Cada módulo se activa o desactiva desde la app y tiene su propia pantalla de configuración. Se programan como **módulos independientes** (en discord.py se llaman *cogs*), para añadirlos por fases. Nota técnica: Discord limita las aplicaciones a 100 comandos de barra principales, por eso los comandos se agrupan en subcomandos (`/mod ban`, `/mod mute`, `/ticket abrir`).

Leyenda de plan: **G** = gratis, **P** = Pro, **B** = Business. Fase: **1** = MVP, **2** = pronto, **3** = avanzado.

### 7.1 Moderación y seguridad
| Módulo | Qué hace | Plan | Fase |
|---|---|---|---|
| Moderación base | Advertir, silenciar (timeout), expulsar, banear, historial de casos | G | 1 |
| Anti-spam | Detecta mensajes repetidos, enlaces masivos y menciones excesivas | G | 1 |
| Anti-raid | Detecta entradas masivas, activa modo bloqueo y avisa a moderadores | P | 2 |
| Moderación con IA | Detecta insultos, acoso y estafas; **sugiere** acciones a los moderadores | P | 2 |
| AutoMod integrado | Usa las reglas nativas de Discord y las configura desde la app | G | 2 |
| Verificación | Botón o captcha para nuevos miembros, con rol de acceso | G | 1 |
| Registros (logs) | Cambios de mensajes, entradas, salidas, roles, canales | G | 1 |
| Apelaciones | Formulario para que un sancionado apele | P | 3 |
| Lista negra de palabras y enlaces | Filtros personalizables | G | 1 |

### 7.2 Comunidad
| Módulo | Qué hace | Plan | Fase |
|---|---|---|---|
| Bienvenida y despedida | Mensajes, imágenes y roles automáticos | G | 1 |
| Roles por reacción o botones | El usuario elige sus roles | G | 1 |
| Niveles y XP | Experiencia por actividad, roles por nivel, clasificación | G | 2 |
| Sorteos | Creación, requisitos, selección verificable de ganadores | G | 2 |
| Encuestas y votaciones | Con botones y resultados en vivo | G | 1 |
| Sugerencias | Canal de ideas con votos y estados | G | 2 |
| Starboard | Destaca los mensajes más populares | G | 3 |
| Contadores | Canales de voz que muestran miembros, en línea, etc. | G | 2 |
| Canales de voz temporales | El usuario crea su sala al entrar a un canal | G | 2 |
| Cumpleaños | Registro y felicitaciones automáticas | G | 2 |
| Recordatorios | Personales y del servidor | G | 2 |
| Anuncios programados | Mensajes en fechas y horas definidas | P | 2 |
| Comandos personalizados y etiquetas | Respuestas fijas creadas por el dueño | G | 2 |
| Traducción | Traduce mensajes entre idiomas | P | 3 |

### 7.3 Tickets y negocio
| Módulo | Qué hace | Plan | Fase |
|---|---|---|---|
| Tickets | Soporte en canales privados, con transcripción | G | 1 |
| Recepcionista IA | Responde y **agenda citas** para negocios con comunidad | P | 3 |
| Solicitudes de staff | Formularios de aplicación con revisión | P | 3 |
| Embudo de ventas | Mensajes y roles para guiar a nuevos miembros a un producto | B | 3 |
| Suscripciones VIP | Roles de pago vinculados a PayPal | B | 3 |

### 7.4 IA
| Módulo | Qué hace | Plan | Fase |
|---|---|---|---|
| Asistente `/pregunta` | Responde con la base de conocimiento del servidor | G | 1 |
| Constructor de servidores | Ver sección 6 | P | 1 |
| Resúmenes de canales | Diarios y semanales | P | 2 |
| Chat con la IA administradora | Órdenes en lenguaje natural desde la app | P | 2 |
| Tutor y coach IA | Responde dudas de estudio, plan de práctica, retroalimentación | P | 3 |
| Creador de CV y cartas | Genera documentos a partir de los datos del usuario | P | 3 |
| Generador de páginas web | Crea una página simple para un negocio y la publica en GitHub Pages | B | 3 |
| Clips de video | Corta momentos de un video largo en formato vertical | B | 3 |
| Publicador en redes | Sube videos a YouTube, TikTok e Instagram mediante un servicio intermediario | B | 3 |

### 7.5 Diversión
| Módulo | Qué hace | Plan | Fase |
|---|---|---|---|
| Economía virtual | Monedas, tienda, trabajos y regalos (solo virtual) | G | 3 |
| Minijuegos | Piedra-papel-tijera, ahorcado, dados, cartas | G | 3 |
| Trivia | Preguntas con puntuación semanal | G | 3 |
| Música (solo fuentes con licencia) | Archivos propios y música libre de derechos | P | 3 |
| Memes y utilidades | Comandos de ocio sin riesgo | G | 3 |

### 7.6 Integraciones
| Módulo | Qué hace | Plan | Fase |
|---|---|---|---|
| Notificaciones de Twitch | Avisa cuando alguien empieza un directo | G | 2 |
| Notificaciones de YouTube | Avisa de videos nuevos | G | 2 |
| Reddit y RSS | Publica novedades de fuentes externas | G | 3 |
| Webhooks y API | Para que otros sistemas hablen con el servidor | B | 3 |

### 7.7 Administración del servidor
| Módulo | Qué hace | Plan | Fase |
|---|---|---|---|
| Copias de seguridad | Guarda y restaura estructura, roles y permisos | P | 2 |
| Plantillas de servidor | Guardar y compartir configuraciones | P | 3 |
| Auditoría de permisos | Detecta permisos peligrosos y los explica | P | 2 |
| Marca blanca | El bot con nombre y avatar del cliente | B | 3 |

---

## 8. El cerebro de IA (capas)

1. **Motor:** Gemini por API. Se usa un modelo rápido y barato para respuestas frecuentes y uno más potente para tareas complejas (como el constructor).
2. **Instrucciones de sistema:** un prompt especializado por tarea (moderación, atención, creación, resumen, tutor).
3. **Base de conocimiento (RAG):** los documentos de cada servidor se dividen en trozos, se convierten en vectores y se buscan por similitud para responder solo con información verificada del servidor.
4. **Memoria:** por servidor (preferencias, tono, reglas) y por usuario (historial corto), con límite de tiempo y borrado a petición.
5. **Herramientas:** funciones que la IA puede pedir ejecutar (crear canal, abrir ticket, silenciar usuario). El sistema las ejecuta **después de validar y, en acciones sensibles, tras la aprobación humana**.
6. **Límites de seguridad:** lista de acciones prohibidas, topes de uso por servidor, filtros de contenido y rechazo de instrucciones que intenten saltarse las reglas.
7. **Evaluación continua:** una lista de 50 a 200 preguntas de prueba con respuestas esperadas que se ejecuta antes de cada actualización de prompts o de modelo.
8. **Observabilidad:** registro de qué respondió la IA, cuánto costó y qué tan útil fue (pulgar arriba o abajo).
9. **Honestidad:** si no sabe, lo dice y deriva a un moderador. Nunca inventa reglas del servidor.
10. **Ajuste fino (opcional, fase 4):** con datos reales y consentimiento de los clientes, se puede ajustar un modelo pequeño para casos muy específicos.

---

## 9. Backend, datos y API

**Tablas principales:** `usuarios`, `servidores`, `modulos_activos`, `configuracion_modulo`, `conocimiento`, `vectores`, `casos_moderacion`, `tickets`, `niveles`, `economia`, `eventos`, `planes_pagos`, `registro_constructor`.

**Endpoints principales:**
- `POST /auth/discord` — inicio de sesión.
- `GET /servidores` — servidores administrables del usuario.
- `POST /servidores/{id}/constructor/plan` — la IA propone un plan.
- `POST /servidores/{id}/constructor/aplicar` — aplica el plan aprobado.
- `POST /servidores/{id}/constructor/deshacer` — revierte.
- `GET/PUT /servidores/{id}/modulos/{modulo}` — configuración de cada módulo.
- `GET/PUT /servidores/{id}/conocimiento` — base de conocimiento.
- `GET /servidores/{id}/analiticas` — métricas.
- `POST /facturacion/suscribir` — inicia el pago.
- `POST /paypal/webhook` — recibe avisos de PayPal.
- `GET /estado` — salud de la API y del bot.

**Comunicación app ↔ bot:** la app habla con la API; la API le pasa órdenes al bot por una cola interna. La app nunca habla directamente con Discord como si fuera el bot.

---

## 10. Cobro: cómo llega el dinero a tu PayPal

### 10.1 La idea
PayPal tiene una cuenta tuya. Cuando un cliente paga, el dinero entra a esa cuenta. Tu servidor solo necesita enterarse del pago para activar el plan.

### 10.2 Configuración paso a paso
1. Crea una cuenta **PayPal Business**.
2. Entra a **developer.paypal.com** → **Apps & Credentials** y crea una app en modo **Sandbox**. Copia el Client ID y el Secret.
3. Crea un **Producto** y los **Planes de suscripción** (Pro y Business) con su precio mensual. Cada plan tiene un `plan_id`.
4. Crea un **Webhook** hacia `https://TU_DOMINIO/paypal/webhook` con los eventos de suscripción (activada, cancelada, suspendida, expirada y pago completado). Copia el Webhook ID.
5. Guarda todo en variables de entorno del servidor.
6. Prueba con cuentas Sandbox. Cuando todo funcione, repite en modo **Live**.

### 10.3 El recorrido de un pago
1. El dueño toca **Mejorar plan** en la app.
2. La API crea la suscripción en PayPal (guardando el id del servidor en `custom_id`) y devuelve el enlace.
3. El dueño aprueba el pago en PayPal.
4. PayPal avisa por **webhook**; la API **verifica la firma** y activa el plan.
5. El bot habilita los módulos del plan.
6. El dinero queda en tu saldo de PayPal y puedes transferirlo a tu banco.

### 10.4 Código de la verificación del webhook (resumen)

```python
import os
import httpx
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()
BASE = os.environ.get("PAYPAL_BASE", "https://api-m.sandbox.paypal.com")


async def token_paypal(client):
    r = await client.post(f"{BASE}/v1/oauth2/token",
                          data={"grant_type": "client_credentials"},
                          auth=(os.environ["PAYPAL_CLIENT_ID"], os.environ["PAYPAL_SECRET"]))
    r.raise_for_status()
    return r.json()["access_token"]


@app.post("/paypal/webhook")
async def webhook(request: Request):
    evento = await request.json()
    h = request.headers
    async with httpx.AsyncClient() as client:
        t = await token_paypal(client)
        v = await client.post(
            f"{BASE}/v1/notifications/verify-webhook-signature",
            headers={"Authorization": f"Bearer {t}"},
            json={"auth_algo": h["paypal-auth-algo"], "cert_url": h["paypal-cert-url"],
                  "transmission_id": h["paypal-transmission-id"],
                  "transmission_sig": h["paypal-transmission-sig"],
                  "transmission_time": h["paypal-transmission-time"],
                  "webhook_id": os.environ["PAYPAL_WEBHOOK_ID"], "webhook_event": evento})
    if v.json().get("verification_status") != "SUCCESS":
        raise HTTPException(400, "Firma inválida")
    guild_id = evento["resource"].get("custom_id")
    if evento["event_type"] == "BILLING.SUBSCRIPTION.ACTIVATED":
        activar_plan(guild_id, evento["resource"]["id"])   # tu función
    elif evento["event_type"] in ("BILLING.SUBSCRIPTION.CANCELLED",
                                  "BILLING.SUBSCRIPTION.SUSPENDED",
                                  "BILLING.SUBSCRIPTION.EXPIRED"):
        desactivar_plan(guild_id)                          # tu función
    return {"ok": True}
```

La creación de la suscripción (`POST /v1/billing/subscriptions` con `plan_id` y `custom_id`) sigue el mismo patrón.

### 10.5 Detalles que importan
- PayPal cobra comisión por cada pago. Consulta las tarifas vigentes.
- Si un pago falla, PayPal suspende la suscripción y avisa por webhook; el servidor vuelve al plan gratis.
- Si algún día publicas la app en App Store o Google Play, esas tiendas exigen su propio sistema de pago para compras digitales dentro de la app. Distribuyendo solo por GitHub y web, no aplica.
- Para empezar a vender antes de automatizar: cobro manual con `paypal.me/TU_USUARIO` y activación a mano.
- Declara tus ingresos según las leyes de tu país.

### 10.6 Planes sugeridos
| Plan | Precio | Incluye |
|---|---|---|
| Gratis | $0 | Módulos básicos, asistente con límite diario |
| Pro | $15–20 al mes | IA ampliada, resúmenes, anti-raid, copias de seguridad, constructor |
| Business | $30–50 al mes | Todo, módulos de negocio, marca blanca, soporte prioritario |
| Instalación | $50–100 una vez | Configuración personalizada del servidor |

---

## 11. Plataformas y distribución

Se escribe la app **una vez en Flutter** y se compila para cada sistema.

| Plataforma | Formato | Dónde se descarga | Costo | Lo que debes saber |
|---|---|---|---|---|
| **Web (PWA)** | Página instalable | URL en GitHub Pages | $0 | Funciona en iPhone, Android, Windows, Mac y ChromeOS. **La vía más fácil para llegar a todos.** |
| **Android** | `.apk` | GitHub Releases | $0 | Hay que permitir instalar de fuentes desconocidas. Google endurece las reglas para desarrolladores no verificados desde septiembre de 2026: revisa los requisitos vigentes. |
| **Windows** | `.zip` / `.msi` | GitHub Releases | $0 | SmartScreen avisa si no está firmado. Firmar cuesta dinero y se puede dejar para después. |
| **macOS** | `.dmg` / `.zip` | GitHub Releases | $0 sin notarizar | macOS bloquea apps sin notarizar; se abre con clic derecho → Abrir. Notarizar requiere el programa de Apple. |
| **Linux** | `.tar.gz` / AppImage | GitHub Releases | $0 | Sin trabas importantes. |
| **iPhone / iPad** | `.ipa` | Ver abajo | $0–$99 al año | La plataforma más restringida. |
| **ChromeOS** | PWA o APK | Web | $0 | Funciona con la PWA. |

**Opciones para iPhone (de mejor a peor para empezar):**
1. **PWA:** abrir la web en Safari → Compartir → "Agregar a pantalla de inicio".
2. **TestFlight** (requiere el programa de desarrolladores de Apple, de pago): permite que mucha gente pruebe la app mediante un enlace.
3. **Tiendas alternativas** (solo donde Apple las permite, como la Unión Europea y Brasil, y con notarización).
4. **Instalar el IPA con herramientas externas:** limitado e incómodo, no apto para el público general.

**Compilación sin computador (GitHub Actions):** un flujo que, al crear la etiqueta `v1.0.0`, compila en servidores de GitHub el APK (Ubuntu), la app de Windows (Windows), la de macOS (macOS), la de Linux (Ubuntu) y la web, y publica todo en **Releases** con sus hashes **SHA-256**. La versión de iPhone se compila con `flutter build ios --release --no-codesign` solo cuando decidas distribuirla. Las claves de firma van en los **Secrets** de GitHub, nunca en el repositorio. ChatGPT debe ajustar el flujo a las versiones actuales de Flutter y de las acciones.

**Actualizaciones:** la app consulta la última versión en GitHub Releases y avisa al usuario. En la web, se actualiza sola.

---

## 12. Repositorio y organización

```
plataforma-ia-discord/
├── README.md              (descargas por plataforma, capturas, video)
├── LICENSE                (MIT)
├── PRIVACY.md
├── SECURITY.md
├── CONTRIBUTING.md
├── assets/                (logo, iconos, capturas)
├── bot/                   (núcleo + módulos: moderacion/, tickets/, niveles/ ...)
├── api/                   (FastAPI)
├── ia/                    (prompts, RAG, evaluaciones)
├── app/                   (Flutter)
├── docs/                  (guías y esta documentación)
├── docker/                (para autoalojar)
├── .env.example
├── .gitignore
└── .github/workflows/     (compilación, pruebas, publicación)
```

**Logo y confianza:** un logo no hace que una app sea segura o peligrosa; sirve para la imagen de marca. Lo que genera confianza es el código visible, el README claro, los lanzamientos con hash, `PRIVACY.md` y `SECURITY.md`.

---

## 13. Seguridad, privacidad y cumplimiento

- Respeta los términos y políticas de desarrolladores de Discord.
- Pide solo los permisos necesarios. Los permisos privilegiados (como leer el contenido de mensajes) requieren aprobación cuando el bot supera los 100 servidores, y pasar esa cifra exige verificar el bot.
- Nunca pongas tokens ni claves en la app ni en el repositorio. Si una clave se filtra, se regenera.
- Verifica siempre la firma de los webhooks de PayPal.
- Guarda los mensajes el menor tiempo posible. Explícalo en `PRIVACY.md` y permite exportar y eliminar datos.
- La IA solo **sugiere** en moderación; un humano decide expulsiones y bloqueos.
- Todas las acciones del constructor son visibles y reversibles.
- Limita el uso por servidor para controlar el costo de la IA y evitar abusos.
- Avisa a los miembros cuando interactúan con una IA.
- Cumple las leyes de protección de datos del país de tus usuarios.

---

## 14. Cómo hacerla famosa

No hay un truco para la fama rápida. Lo que funciona de forma repetible:

### 14.1 Plan de 90 días
**Días 1–14:** termina el MVP (fase 1) y grábalo funcionando con la grabación de pantalla del teléfono. Publica el repositorio con un README atractivo.

**Días 15–30:** instala el bot gratis en 3 a 5 servidores y pide testimonios. Comparte en comunidades de Discord, Reddit (Python, Discord, autoalojamiento) y X, **aportando ayuda real**, no solo enlaces. Responde cada problema que abran en GitHub.

**Días 31–60:** publica los videos de abajo. Ofrece el plan Pro a los servidores donde ya funciona.

**Días 61–90:** lanza la PWA y los instaladores. Publica casos de éxito ("este servidor ahorró X horas"). Si hay ingresos, paga la cuenta de Apple para iPhone.

### 14.2 Qué hace crecer un proyecto abierto
- Un caso de uso claro en una frase.
- Una demostración corta de 20 segundos.
- Instalación en 3 pasos.
- Responder rápido a quienes lo prueban.
- Publicar mejoras con frecuencia.
- Aparecer donde ya está tu público, ayudando antes de promocionar.

### 14.3 Cuatro videos (sirven para TikTok, YouTube Shorts e Instagram Reels)
Cada video es vertical (9:16) y dura entre 20 y 40 segundos. Se graban con la pantalla del teléfono y se editan con subtítulos automáticos en CapCut. Los mismos guiones sirven en las tres plataformas; solo cambian el título, la descripción y los hashtags.

1. **"Creé un servidor entero con una frase"**
   - Gancho: "Le dije a la IA 'quiero una comunidad de inglés' y mira lo que pasó."
   - Cuerpo: el asistente propone el plan, la vista previa y el botón Aplicar.
   - Cierre: "Es gratis y de código abierto."
2. **"Tu bot de Discord, pero con IA"**
   - Gancho: "Esta IA responde a tu comunidad, modera y resume el día."
   - Cuerpo: `/pregunta`, un resumen diario y un ticket.
   - Cierre: "Pruébalo en tu servidor."
3. **"Hecho desde un teléfono"**
   - Gancho: "Construí esto sin computador."
   - Cuerpo: el teléfono con Termux y GitHub.
   - Cierre: "¿Quieres el tutorial?"
4. **"Una app para todos tus dispositivos"**
   - Gancho: "Controla tu servidor desde Android, iPhone, Windows o Mac."
   - Cuerpo: la app en varias pantallas.
   - Cierre: "Descarga gratis desde GitHub."

> Este documento solo trae los guiones. Los videos hay que grabarlos y editarlos.

---

## 15. Costos e ingresos realistas

**Costos al empezar:** casi cero (GitHub, Gemini con uso bajo, hosting gratuito o muy barato, PayPal solo cobra comisión por venta). Cuando haya clientes: hosting que se mantenga encendido, base de datos y consumo de Gemini. Calcula el costo de IA por servidor para que cada plan deje margen.

**Ingresos:**
- $100 al día son unos $3,000 al mes: unos 100 servidores a $30 o unos 200 a $15.
- Los primeros pagos suelen llegar en semanas; el volumen alto, en meses.
- Los $1,000 diarios no son una meta realista para un producto solo, y nadie puede garantizarlos.
- La mayoría de los micro-SaaS no supera los $1,000 mensuales; el nicho y la constancia marcan la diferencia.

---

## 16. Hoja de ruta por fases (para no quedarse a medias)

Una plataforma así es enorme. Se construye por etapas y se **cobra desde la fase 1**.

**Fase 1 — MVP (semanas 1–4)**
- Bot con: bienvenida, `/pregunta` con base de conocimiento, moderación base, anti-spam, verificación, registros, roles por botones, encuestas, tickets.
- Constructor de servidores con IA (con vista previa y deshacer).
- API básica, inicio de sesión con Discord y PayPal en modo de pruebas.
- App web (PWA) con las pantallas 1–11, 14–17, 19–22, 28, 34 y 37.

**Fase 2 — Crecimiento (meses 2–3)**
- Anti-raid, moderación con IA, niveles, sorteos, sugerencias, contadores, voz temporal, cumpleaños, recordatorios, anuncios programados.
- Resúmenes, chat con la IA administradora, copias de seguridad, auditoría de permisos, Twitch y YouTube.
- Android (APK) y escritorio (Windows, Mac, Linux).
- PayPal en modo real.

**Fase 3 — Plataforma (meses 4–6)**
- Economía virtual, minijuegos, trivia, música con licencia, traducción, comandos personalizados.
- Recepcionista, solicitudes de staff, VIP con PayPal, marca blanca.
- Tutor, CV, páginas web, clips y publicación en redes.
- iPhone vía TestFlight si hay ingresos.

**Fase 4 — Escala**
- Verificación del bot con Discord, PostgreSQL, múltiples instancias, ajuste fino opcional de un modelo propio.

---

## 17. Instrucciones para ChatGPT y complementos que debe conectar

> Esta es la última sección. Pégale a ChatGPT todo el documento y pídele que lo siga **fase por fase**, empezando por la fase 1.

### 17.1 Qué debe hacer ChatGPT
1. Leer este documento completo y confirmar cuál es la fase 1 antes de escribir código.
2. Con el repositorio ya creado, generar la estructura de la sección 12.
3. Construir la fase 1: bot con los módulos indicados, constructor de servidores (sección 6), API y la app web.
4. Escribir las instrucciones de sistema, la base de conocimiento con búsqueda y las pruebas de evaluación de la sección 8. **Usar un modelo ya entrenado (Gemini por API); no intentar entrenar un modelo desde cero.**
5. Crear el diseño de la app según la sección 5, con todas las pantallas de la fase 1.
6. Escribir los flujos de GitHub Actions para compilar la web, Android, Windows, macOS y Linux, ajustados a las versiones actuales.
7. Redactar `README.md`, `PRIVACY.md`, `SECURITY.md`, `CONTRIBUTING.md` y `LICENSE` (MIT).
8. Generar el logo y los iconos en `assets/`.
9. Mantener un archivo `ESTADO.md` con lo hecho, lo pendiente y los problemas encontrados.
10. **Avisar claramente** de cada paso que no pueda hacer él mismo.
11. No poner nunca tokens ni claves en el código ni en el repositorio.

### 17.2 Complementos y conexiones que necesita
Las opciones cambian según el plan y la fecha. Revísalas en la configuración de ChatGPT.
- **GitHub:** para leer y escribir en el repositorio y ejecutar los flujos de compilación. Dale acceso solo a este repositorio.
- **Ejecución de código o entorno de archivos:** para probar el código y generar archivos.
- **Generación de imágenes:** para el logo, los iconos y las capturas de diseño.
- **Navegación web:** para revisar la documentación vigente de Discord, Gemini, PayPal, Flutter, Google y Apple.

### 17.3 Lo que harás tú a mano
- Crear el repositorio y dar el acceso a ChatGPT.
- Crear la aplicación y el bot en el portal de desarrolladores de Discord y poner el token en el servidor.
- Conseguir la clave de Gemini.
- Crear la cuenta de PayPal Business, las claves, los planes y el webhook.
- Contratar el hosting cuando haya ingresos.
- Pagar la cuenta de desarrollador de Apple, si decides distribuir en iPhone.
- Grabar y publicar los videos
