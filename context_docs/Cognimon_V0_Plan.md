# Cognimon V0 --- Plan de Prototipo Inicial

## 1. Visión del prototipo

**Cognimon V0** será una criatura digital que vive directamente en el
escritorio de Windows.

El objetivo del primer prototipo no es construir todavía un asistente de
IA completo, sino demostrar que Cognimon puede:

-   aparecer sobre el escritorio;
-   permanecer visible como una criatura independiente de las ventanas
    normales;
-   animarse en estado `idle`;
-   caminar de forma sencilla por el escritorio;
-   reaccionar al clic del usuario;
-   mostrar diálogos mediante burbujas estilo cómic;
-   recibir texto del usuario;
-   conectarse a Ollama;
-   generar respuestas con una personalidad propia;
-   cambiar de animación mientras "piensa" y "habla";
-   volver a su comportamiento normal después de interactuar.

### Objetivo conceptual

El prototipo debe conseguir la sensación:

> **"Tengo una criatura digital viviendo en mi PC."**

------------------------------------------------------------------------

# 2. Alcance de Cognimon V0

## Incluido

-   Aplicación de escritorio en Python.
-   PySide6 para la interfaz.
-   Ventana transparente y sin bordes.
-   Cognimon como personaje 2D.
-   Animaciones básicas mediante sprites.
-   Movimiento horizontal/aleatorio.
-   Interacción mediante mouse.
-   Burbujas de diálogo estilo cómic.
-   Campo de texto para conversar.
-   Integración con Ollama.
-   Prompt inicial de personalidad.
-   Estados básicos del personaje.

## Fuera del alcance de V0

No implementar todavía:

-   voz;
-   TTS;
-   reconocimiento de voz;
-   memoria persistente;
-   RAG;
-   base de datos;
-   sistema de evolución;
-   emociones complejas;
-   visión por computadora;
-   herramientas externas;
-   navegación web;
-   integración con ESP32;
-   sistema multiagente;
-   entrenamiento de modelos;
-   animación 3D.

Estas características podrán formar parte de versiones posteriores.

------------------------------------------------------------------------

# 3. Experiencia objetivo

Cuando el usuario inicia Cognimon:

1.  Cognimon aparece en el escritorio.
2.  Ejecuta una animación `idle`.
3.  Después de cierto tiempo puede comenzar a caminar.
4.  Se detiene aleatoriamente.
5.  El usuario puede hacer clic sobre él.
6.  Aparece una burbuja de diálogo.
7.  El usuario puede escribir una pregunta.
8.  Cognimon cambia a estado `thinking`.
9.  Ollama genera una respuesta.
10. Cognimon muestra la respuesta en una burbuja estilo cómic.
11. Cognimon utiliza una animación `talking`.
12. Después vuelve a `idle`.

------------------------------------------------------------------------

# 4. Arquitectura general

``` text
                    COGNIMON V0
                         │
              ┌──────────┴──────────┐
              │                     │
        CHARACTER ENGINE        AI ENGINE
              │                     │
        ┌─────┼─────┐           Ollama
        │     │     │               │
      Idle  Walk  Talking        Local LLM
        │     │     │               │
        └─────┼─────┘               │
              │                     │
              └──────────┬──────────┘
                         │
                    UI / DESKTOP
                         │
              ┌──────────┼──────────┐
              │          │          │
          Character   Bubble      Input
```

------------------------------------------------------------------------

# 5. Tecnologías

## Lenguaje

**Python**

Será el lenguaje principal del proyecto.

## Interfaz

**PySide6**

Se utilizará para:

-   crear la ventana transparente;
-   gestionar eventos del mouse;
-   mostrar imágenes;
-   crear burbujas;
-   crear el campo de texto;
-   controlar timers;
-   gestionar la posición del personaje.

## LLM

**Ollama**

Será el cerebro de Cognimon durante el prototipo.

La comunicación será local:

``` text
Cognimon App
     │
     ▼
 Ollama
     │
     ▼
 Local LLM
     │
     ▼
 Response
```

## Assets

Imágenes PNG con transparencia.

------------------------------------------------------------------------

# 6. Estados de Cognimon

El sistema debe utilizar una máquina de estados sencilla.

``` text
             ┌──────────┐
             │   IDLE   │
             └────┬─────┘
                  │
          tiempo / comportamiento
                  │
                  ▼
             ┌──────────┐
             │  WALK    │
             └────┬─────┘
                  │
               detener
                  │
                  ▼
             ┌──────────┐
             │   IDLE   │
             └────┬─────┘
                  │
                click
                  │
                  ▼
             ┌──────────┐
             │ TALKING  │
             └────┬─────┘
                  │
             usuario escribe
                  │
                  ▼
             ┌──────────┐
             │ THINKING │
             └────┬─────┘
                  │
            Ollama responde
                  │
                  ▼
             ┌──────────┐
             │ TALKING  │
             └────┬─────┘
                  │
                  ▼
             ┌──────────┐
             │   IDLE   │
             └──────────┘
```

## Estados iniciales

### IDLE

Cognimon permanece en su sitio.

Comportamientos posibles:

-   parpadear;
-   movimiento ligero;
-   cambiar ligeramente de postura.

### WALK

Cognimon se desplaza por el escritorio.

### THINKING

Mientras Ollama procesa la pregunta:

-   Cognimon cambia de expresión;
-   aparece una animación de pensamiento;
-   puede aparecer una pequeña indicación visual como `...`.

### TALKING

No habrá audio en V0.

La animación `talking` servirá para dar la impresión visual de que
Cognimon está hablando.

------------------------------------------------------------------------

# 7. Assets necesarios

La primera versión del personaje debe utilizar sprites 2D.

## Estructura

``` text
assets/
└── cognimon/
    ├── idle/
    │   ├── idle_01.png
    │   ├── idle_02.png
    │   ├── idle_03.png
    │   └── idle_04.png
    │
    ├── walk/
    │   ├── walk_01.png
    │   ├── walk_02.png
    │   ├── walk_03.png
    │   └── walk_04.png
    │
    ├── thinking/
    │   ├── thinking_01.png
    │   ├── thinking_02.png
    │   └── thinking_03.png
    │
    └── talking/
        ├── talking_01.png
        ├── talking_02.png
        └── talking_03.png
```

## Prioridad de assets

Para comenzar no es necesario tener todos los sprites.

Orden recomendado:

1.  `idle`
2.  `walk`
3.  `thinking`
4.  `talking`

Incluso se puede comenzar con una sola imagen de Cognimon para probar la
ventana transparente.

------------------------------------------------------------------------

# 8. Ventana de escritorio

La ventana de Cognimon debe sentirse como parte del escritorio y no como
una ventana tradicional.

Características:

-   transparente;
-   sin bordes;
-   sin barra de título;
-   siempre encima;
-   tamaño ajustado al personaje;
-   fondo invisible;
-   interacción con mouse;
-   posibilidad de cambiar posición.

Conceptualmente:

``` text
┌──────────────────────────────────────────────┐
│                                              │
│                         🔵                   │
│                      Cognimon                │
│                                              │
│                                              │
└──────────────────────────────────────────────┘

Las áreas transparentes no deben ser visibles.
```

------------------------------------------------------------------------

# 9. Movimiento

El movimiento inicial no necesita IA.

Cognimon tendrá:

-   posición `x`;
-   posición `y`;
-   velocidad;
-   dirección;
-   límites de movimiento.

Ejemplo conceptual:

``` text
Cognimon
    │
    ├── x
    ├── y
    ├── speed
    └── direction
```

Comportamiento inicial:

``` text
IDLE
  ↓
esperar
  ↓
WALK
  ↓
moverse
  ↓
llegar a una posición
  ↓
IDLE
```

Más adelante podrán añadirse comportamientos como:

-   mirar alrededor;
-   reaccionar al mouse;
-   acercarse al cursor;
-   esconderse;
-   dormir;
-   jugar;
-   buscar una esquina del escritorio.

------------------------------------------------------------------------

# 10. Interacción con el usuario

## Click izquierdo

Al hacer clic sobre Cognimon:

-   detener movimiento;
-   mostrar burbuja;
-   abrir interacción.

## Click derecho

Menú contextual inicial:

``` text
┌──────────────────────┐
│ Hablar               │
│                      │
│ Dormir               │
│                      │
│ Salir                │
└──────────────────────┘
```

## Input

El usuario podrá escribir:

``` text
┌──────────────────────────────────────┐
│ Escribe algo...                  ➤  │
└──────────────────────────────────────┘
```

------------------------------------------------------------------------

# 11. Sistema de diálogo

El diálogo no será inicialmente un chat convencional.

Debe parecer una conversación de personaje.

## Cognimon hablando

``` text
          ┌─────────────────────────────┐
          │ ¡Hola! Soy Cognimon.        │
          └──────────────┬──────────────┘
                         ╲╱
                       COGNIMON
```

## Usuario preguntando

``` text
      ┌─────────────────────────┐
      │ ¿Qué es Python?         │
      └────────────┬────────────┘
                   ╲╱
```

## Respuesta

``` text
                 COGNIMON

      ┌──────────────────────────────┐
      │ Python es un lenguaje de     │
      │ programación...              │
      └──────────────────────────────┘
```

## Requisitos

Las burbujas deben:

-   aparecer suavemente;
-   ajustarse al tamaño del texto;
-   tener un límite de longitud;
-   posicionarse cerca de Cognimon;
-   desaparecer después de un tiempo o al continuar la conversación.

------------------------------------------------------------------------

# 12. Integración con Ollama

La aplicación tendrá un módulo independiente:

``` text
ai/
└── ollama_client.py
```

Responsabilidad:

1.  recibir el mensaje del usuario;
2.  enviarlo a Ollama;
3.  recibir la respuesta;
4.  devolver únicamente el texto a la aplicación.

Conceptualmente:

``` text
Usuario
   │
   ▼
Chat Input
   │
   ▼
Ollama Client
   │
   ▼
Ollama
   │
   ▼
LLM
   │
   ▼
Response
   │
   ▼
Speech Bubble
```

La aplicación no debe depender directamente de detalles internos del
modelo.

------------------------------------------------------------------------

# 13. Personalidad inicial

Cognimon debe sentirse como una criatura, no como un chatbot genérico.

Características:

-   inteligente;
-   analítico;
-   curioso;
-   amigable;
-   ligeramente juguetón;
-   interesado en resolver problemas;
-   capaz de expresar sorpresa;
-   capaz de admitir que no sabe algo.

## Prompt conceptual

``` text
You are Cognimon.

You are a small digital creature that lives on the user's desktop.

You are intelligent, analytical, curious, friendly and slightly playful.

You enjoy solving problems and learning new things.

You are not a generic AI assistant.
You behave like a digital creature with a personality.

Your responses should be relatively short because they appear
inside comic-style speech bubbles.

You can express curiosity, excitement, confusion and satisfaction.

When appropriate, ask questions instead of always providing
the complete answer immediately.
```

El prompt real se irá refinando durante las pruebas.

------------------------------------------------------------------------

# 14. Estructura del proyecto

La primera implementación debe mantener los componentes separados.

``` text
cognimon/
│
├── main.py
│
├── character/
│   ├── cognimon.py
│   ├── animation.py
│   ├── movement.py
│   └── states.py
│
├── ai/
│   ├── ollama_client.py
│   └── prompt.py
│
├── ui/
│   ├── desktop.py
│   ├── speech_bubble.py
│   └── chat_input.py
│
├── assets/
│   └── cognimon/
│       ├── idle/
│       ├── walk/
│       ├── thinking/
│       └── talking/
│
├── config/
│   └── config.json
│
└── requirements.txt
```

------------------------------------------------------------------------

# 15. Plan de implementación

## V0.0.1 --- Ventana

Objetivo:

> Cognimon aparece en el escritorio.

Implementar:

-   proyecto Python;
-   PySide6;
-   ventana transparente;
-   ventana sin bordes;
-   imagen PNG;
-   posición inicial;
-   always-on-top.

### Resultado esperado

Cognimon aparece como una criatura sobre el escritorio.

------------------------------------------------------------------------

## V0.0.2 --- Idle

Objetivo:

> Cognimon parece estar vivo.

Implementar:

-   sprite animation;
-   timer;
-   cambio de frames;
-   parpadeo;
-   pequeño movimiento.

### Resultado esperado

Cognimon permanece en el escritorio animándose.

------------------------------------------------------------------------

## V0.0.3 --- Movimiento

Objetivo:

> Cognimon puede caminar por el escritorio.

Implementar:

-   movimiento horizontal;
-   dirección;
-   velocidad;
-   límites;
-   cambio de animación;
-   pausas aleatorias.

### Resultado esperado

Cognimon camina, se detiene y vuelve a caminar.

------------------------------------------------------------------------

## V0.0.4 --- Interacción

Objetivo:

> El usuario puede interactuar con Cognimon.

Implementar:

-   detección de click;
-   detener movimiento;
-   speech bubble;
-   input de texto;
-   menú contextual básico.

### Resultado esperado

El usuario puede hacer clic en Cognimon y comenzar una conversación.

------------------------------------------------------------------------

## V0.0.5 --- Ollama

Objetivo:

> Cognimon tiene un cerebro.

Implementar:

-   conexión con Ollama;
-   configuración del modelo;
-   prompt de Cognimon;
-   envío de mensajes;
-   recepción de respuestas;
-   manejo básico de errores.

### Resultado esperado

El usuario escribe una pregunta y Cognimon responde.

------------------------------------------------------------------------

## V0.0.6 --- Thinking

Objetivo:

> Cognimon parece estar procesando la información.

Implementar:

-   estado `THINKING`;
-   animación;
-   indicador `...`;
-   bloqueo temporal del input;
-   transición a `TALKING`.

### Resultado esperado

``` text
Pregunta
   ↓
THINKING
   ↓
Ollama
   ↓
TALKING
   ↓
IDLE
```

------------------------------------------------------------------------

## V0.0.7 --- Talking

Objetivo:

> Cognimon parece hablar.

Implementar:

-   animación `talking`;
-   mostrar respuesta;
-   sincronizar duración aproximada con la aparición del texto;
-   transición automática a `idle`.

No habrá audio.

### Resultado esperado

Cognimon cambia de expresión mientras muestra su respuesta.

------------------------------------------------------------------------

# 16. Flujo completo de V0

``` text
                INICIO
                   │
                   ▼
             COGNIMON SPAWN
                   │
                   ▼
                 IDLE
                   │
             ┌─────┴─────┐
             │           │
          caminar      click
             │           │
             ▼           ▼
           WALK       INTERACT
             │           │
             └─────┐     ▼
                   │   INPUT
                   │     │
                   │     ▼
                   │  THINKING
                   │     │
                   │   Ollama
                   │     │
                   │     ▼
                   │  TALKING
                   │     │
                   └─────┴──────► IDLE
```

------------------------------------------------------------------------

# 17. Criterios de éxito

Cognimon V0 será considerado funcional cuando:

-   [ ] La aplicación se ejecuta como programa de escritorio.
-   [ ] Cognimon aparece con fondo transparente.
-   [ ] No existe una ventana tradicional alrededor del personaje.
-   [ ] Cognimon permanece encima del escritorio.
-   [ ] Cognimon tiene una animación `idle`.
-   [ ] Cognimon puede caminar.
-   [ ] Cognimon puede detenerse.
-   [ ] Cognimon responde al clic.
-   [ ] Aparece una burbuja estilo cómic.
-   [ ] El usuario puede introducir texto.
-   [ ] Ollama recibe el mensaje.
-   [ ] Cognimon recibe la respuesta.
-   [ ] Cognimon cambia a `thinking`.
-   [ ] Cognimon cambia a `talking`.
-   [ ] La respuesta aparece como diálogo.
-   [ ] Cognimon vuelve a `idle`.
-   [ ] La aplicación puede cerrarse correctamente.

------------------------------------------------------------------------

# 18. Filosofía de desarrollo

El proyecto debe construirse de forma incremental.

No intentar desarrollar Cognimon completo desde el inicio.

La prioridad será:

``` text
PERSONAJE
   ↓
MOVIMIENTO
   ↓
INTERACCIÓN
   ↓
DIÁLOGO
   ↓
LLM
   ↓
PERSONALIDAD
```

Primero debemos conseguir que **Cognimon exista físicamente en el
escritorio**.

Después debemos conseguir que **se comporte como una criatura**.

Finalmente debemos conseguir que **piense y converse**.

------------------------------------------------------------------------

# 19. Próximo objetivo

El primer objetivo práctico será construir:

## Cognimon V0.0.1

Un proyecto mínimo:

``` text
Python
  +
PySide6
  +
PNG transparente
  =
Cognimon en el escritorio
```

Sin Ollama.

Sin chat.

Sin voz.

Sin memoria.

Sin evolución.

Solamente:

> **Una criatura azul viviendo en el escritorio de Windows.**

Una vez que esta base funcione correctamente, se construirá V0.0.2 sobre
ella sin reescribir el sistema anterior.
