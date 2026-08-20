# Etapa 2 — Memoria: Plan de Implementación

Basado en `context_docs/etapa_2.md` (la especificación completa de Etapa 2, no solo el resumen de `Digiminds_Roadmap(1).md`). Ese documento pide explícitamente:

- 4 tipos de memoria: **Short-Term, Long-Term, Episodic, Semantic**.
- Un pipeline de formación (`Conversation → Memory Analyzer → Important? → Create Memory → Store`).
- Importancia, recencia y un `Memory Score`, sin borrado automático de información importante.
- Almacenamiento híbrido: **SQLite + Vector DB + Files**.
- Un componente `MemoryManager` con `remember / recall / forget / update / summarize / consolidate / score`.
- Consolidación de memorias relacionadas y manejo de contradicciones.
- Privacidad local-first: el usuario puede ver, editar, eliminar, exportar, importar y desactivar su memoria.

Este plan traduce eso a cambios concretos sobre el código real del repo.

------------------------------------------------------------------------

## 1. Estado actual (gap real)

`ai/ollama_client.py` hoy manda únicamente `[system_prompt, mensaje_nuevo]` en cada `ask()`. No hay historial de conversación (ni corto plazo), no hay persistencia (no existe `data/`), y la Etapa 1 (V0.5 — Digital Core) tampoco está construida todavía. Este plan no espera a que exista un Digital Core completo: construye el subconjunto de persistencia/identidad mínimo que la memoria necesita, de forma que encaje como un campo más del Digital Core el día que se implemente completo.

------------------------------------------------------------------------

## 2. Decisiones de arquitectura (para validar antes de empezar)

`etapa_2.md` pide SQLite + Vector DB + Files como tres piezas separadas. Antes de escribir código conviene decidir qué tan literal se toma eso:

- **SQLite en vez de tres motores separados.** Propongo usar **una sola base SQLite** (`sqlite3`, viene con Python, cero dependencias nuevas) para todo lo estructurado *y* para los embeddings: cada memoria guarda su vector como BLOB en la misma fila. Con el volumen de memorias que un Digimind personal genera (cientos, no millones), calcular similitud coseno en Python/NumPy sobre esa columna es instantáneo — no hace falta un motor de vector search dedicado (Chroma/FAISS/etc). Si el volumen crece mucho en el futuro, migrar `recall()` a un motor real es un cambio contenido porque queda detrás de la interfaz de `MemoryManager`. **Este es el punto donde más me aparto del diagrama original del documento — avisame si preferís mantener un vector store separado desde el día uno.**
- **Embeddings vía Ollama**, reutilizando la conexión que ya existe (`/api/embeddings`, ej. modelo `nomic-embed-text`) — no se suma un proveedor externo ni una librería de embeddings nueva.
- **Files** para las transcripciones completas de conversación (`data/<character>/conversations/<YYYY-MM-DD>.jsonl`), que alimentan `summarize()` sin tener que guardar cada charla dentro de SQLite.
- **Identidad mínima**: una tabla `identity` de una fila (id, nombre, especie, fecha de creación) — cubre "Identificación única del Digimind" y "Persistencia entre sesiones" del Definition of Done sin construir personalidad/evolución (eso es Etapa 1/3/7).
- **Editar/exportar/importar memoria** (pedido en la sección de privacidad) es difícil directamente sobre SQLite. Se resuelve con `MemoryManager.export_json()` / `import_json()`: vuelcan/cargan el contenido como JSON legible, que el usuario puede editar a mano y volver a importar.

------------------------------------------------------------------------

## 3. Esquema de datos

```text
data/
├── cognimon/
│   ├── memory.db              (SQLite: identity + memories)
│   └── conversations/
│       └── 2026-08-20.jsonl   (turnos crudos, para summarize())
└── curimon/
    ├── memory.db
    └── conversations/
```

Tabla `identity` (una fila):

```text
id | name | species | created_at
```

Tabla `memories`:

```text
id                 TEXT PK (uuid)
type               TEXT   -- 'long_term' | 'episodic' | 'semantic'
content             TEXT   -- texto en tercera persona, ej. "The user's robot is named Atlas."
metadata            TEXT   -- JSON: para episodic {event, context, outcome, emotional_context}
tags                TEXT   -- JSON array, ej. ["robot", "atlas", "esp32"]
importance          REAL   -- 0.0–1.0
status              TEXT   -- 'permanent' | 'long_term' | 'temporary'
embedding           BLOB   -- vector float32 empaquetado
created_at          TEXT   -- ISO date
last_referenced_at  TEXT   -- ISO date, se actualiza en cada recall() que la use
superseded_by       TEXT   -- id de otra memoria, nullable (contradicciones/consolidación)
```

`Short-Term Memory` **no se persiste** en esta tabla — vive como una lista en memoria de proceso (últimos N turnos), tal como pide el documento ("no necesariamente debe conservarse permanentemente").

`Semantic Memory` no se llena turno a turno: es el *resultado* de `consolidate()` agrupando varias `long_term`/`episodic` relacionadas (ver Fase 6). Por eso aparece tarde en las fases, aunque el tipo de dato exista desde la Fase 0.

------------------------------------------------------------------------

## 4. Fases de implementación

### V0.6.0 — Fundaciones: identidad + `MemoryManager` + SQLite

Objetivo:

> Existe un lugar donde el Digimind puede guardar y leer datos propios.

Implementar:

- `memory/db.py`: creación del esquema SQLite (`identity`, `memories`), una conexión por personaje en `data/<character>/memory.db`.
- `memory/manager.py`: clase `MemoryManager(character_name)` con los métodos de la API (`remember`, `recall`, `forget`, `update`, `summarize`, `consolidate`, `score`) — arrancan como esqueletos que las fases siguientes van completando.
- Al iniciar `CreatureWindow` (`ui/desktop.py`), crear/leer la identidad (nombre = `character_name`, `created_at` la primera vez que se ve ese personaje).
- `data/` agregado a `.gitignore` (es estado personal del usuario, no debe versionarse).

### Resultado esperado

`data/cognimon/memory.db` existe después de correr `python main.py --cognimon` una vez, con una fila de identidad.

------------------------------------------------------------------------

### V0.6.1 — Short-Term Memory (contexto de la conversación actual)

Objetivo:

> Cognimon recuerda lo que se dijo dentro de la misma conversación.

Implementar:

- `OllamaClient` mantiene un historial interno (`self._history`, últimos N turnos `{role, content}`), no persistido.
- `ask()` arma `messages = [system] + history + [mensaje nuevo]`.
- Cada turno (usuario + respuesta) también se apenda a `data/<character>/conversations/<hoy>.jsonl` (Files) — esto no es memoria todavía, es la materia prima que `summarize()` usará en la Fase 5.

### Resultado esperado

Dentro de una misma sesión, una referencia implícita al mensaje anterior ("¿y eso funcionó?") tiene sentido para Cognimon.

------------------------------------------------------------------------

### V0.6.2 — Memory Formation: el Memory Analyzer

Objetivo:

> Cognimon decide solo qué merece recordarse — no todo lo que se dice.

Este es el paso `Conversation → Memory Analyzer → Important? → Create Memory → Store` del documento.

Implementar:

- Después de cada respuesta, un segundo llamado liviano a Ollama (prompt distinto al de la personalidad) que recibe el último intercambio y devuelve algo como:
  ```json
  {"memorable": true, "memories": [
    {"type": "long_term", "content": "The user's robot is named Atlas.", "tags": ["robot","atlas"], "importance": 0.85}
  ]}
  ```
- Parseo defensivo: si el modelo local no devuelve JSON válido, no se crea memoria y la respuesta visible no se ve afectada — la extracción es best-effort, nunca bloqueante.
- `MemoryManager.remember(...)` persiste cada memoria nueva vía `memory/db.py`.
- **Trade-off a decidir con vos:** esto cuesta una llamada extra a Ollama por mensaje (latencia). La alternativa más barata es la que usé en el plan anterior (que el propio modelo agregue un tag `[MEMORY: ...]` al final de su respuesta normal, sin segunda llamada) — más rápida pero menos confiable para clasificar tipo/importancia. Empezaría con la llamada dedicada porque el diagrama del documento la pide como paso separado, y es más fácil de optimizar después que de hacer confiable después.

### Resultado esperado

"Mi robot se llama Atlas" queda guardado como memoria `long_term` con importancia alta, sin acción manual del usuario.

------------------------------------------------------------------------

### V0.6.3 — Embeddings + Retrieval semántico (`recall()`)

Objetivo:

> Cognimon encuentra lo relevante aunque el usuario no repita las palabras exactas.

Implementar:

- Al crear una memoria (`remember()`), calcular su embedding vía Ollama y guardarlo en la columna `embedding`.
- `MemoryManager.recall(query, k=5)`: embedding del mensaje nuevo → similitud coseno contra todas las memorias (NumPy) → top-K candidatas.
- Actualiza `last_referenced_at` de las memorias recuperadas.

### Resultado esperado

Preguntar "¿cómo va el proyecto del robot?" encuentra la memoria de Atlas aunque el usuario no diga "Atlas" literalmente (ejemplo textual del documento, sección 10).

------------------------------------------------------------------------

### V0.6.4 — Context Builder: integración real con el LLM

Objetivo:

> Nunca se manda toda la memoria al LLM — solo lo relevante.

Implementar:

- `ai/context_builder.py` (nuevo, pequeño): dado un mensaje nuevo, junta `recall()` (memorias relevantes) + historial de corto plazo + system prompt, y arma el payload final para `OllamaClient.ask()`.
- Extender `system_prompt()` (`ai/prompt.py`) para aceptar el bloque de memorias relevantes ("Cosas que recordás del usuario: ...").
- `ui/desktop.py._on_message_submitted` pasa por el Context Builder antes de llamar a Ollama.

### Resultado esperado

Reproduce el flujo completo del documento: `User Message → Memory Retrieval → Context Builder → LLM`.

------------------------------------------------------------------------

### V0.6.5 — Importance, Recency y Memory Score

Objetivo:

> Las memorias más importantes y recientes pesan más al recuperar, pero nada importante se borra solo.

Implementar:

- `MemoryManager.score(memory, query)` = `importance × relevancia_semántica × recency`, con `recency` como decaimiento exponencial suave sobre `last_referenced_at` (con piso, para que memorias `status="permanent"` no pierdan casi peso).
- `recall()` usa `score()` para el ranking final, no solo similitud coseno cruda.
- **Explícitamente NO se borra nada automáticamente** — `status` (`permanent`/`long_term`/`temporary`) solo afecta el ranking; borrar es una acción manual (Fase 7, `forget()` invocado por el usuario, o por `consolidate()` cuando reemplaza duplicados por una versión mejor).

### Resultado esperado

Una memoria marcada `importance: 0.95` sigue apareciendo en resultados meses después; una de `importance: 0.10` deja de aparecer aunque coincida por palabras clave.

------------------------------------------------------------------------

### V0.6.6 — Consolidación y contradicciones

Objetivo:

> La memoria se vuelve más limpia con el tiempo en vez de acumular duplicados o verdades viejas.

Implementar:

- `MemoryManager.consolidate()`: agrupa memorias `long_term`/`episodic` relacionadas (por tags + similitud de embedding), pide a Ollama que las resuma en una sola memoria `semantic` (ej. cuatro menciones de "usa Python" → "El usuario usa Python frecuentemente, sobre todo para robótica e IA"), marca las originales con `superseded_by` apuntando a la nueva en vez de borrarlas (conserva historial).
- `MemoryManager.update(memory_id, new_content)`: cuando el Memory Analyzer (Fase 2) detecta que un hecho nuevo contradice uno existente (alta similitud + contenido incompatible), en vez de crear una memoria suelta, marca la vieja como superseded y crea la nueva enlazada — igual que el ejemplo de Ollama → "Runtime X" del documento.
- Disparo: manual por ahora (acción de menú "Consolidar memoria"), no automático en cada mensaje — correr esto en cada turno sería costoso y es una operación de mantenimiento, no de conversación.

### Resultado esperado

Cuatro memorias sueltas sobre Python se convierten en una memoria `semantic` limpia; cambiar de Ollama a otro runtime actualiza el hecho en vez de duplicarlo.

------------------------------------------------------------------------

### V0.6.7 — Privacidad y control del usuario

Objetivo:

> La memoria le pertenece al usuario, no a la app.

Implementar (extendiendo el menú contextual ya existente en `ui/desktop.py`, junto a Hablar/Dab/Shooting/Dormir/Salir):

- **Ver memorias** — lista simple (consola o un diálogo mínimo) de las memorias guardadas.
- **Borrar toda la memoria** — vacía `memory.db` para ese personaje (con confirmación, es destructivo).
- **Exportar memoria** — `MemoryManager.export_json(path)` vuelca todo a un JSON legible.
- **Importar memoria** — `MemoryManager.import_json(path)` carga ese JSON (permite editar a mano y reimportar).
- **Desactivar memoria** — flag de sesión que salta `recall()` y `remember()` sin perder lo ya guardado.

No se construye una UI gráfica dedicada (el mockup del documento) en esta fase — se resuelve con el menú contextual que ya existe, que es coherente con lo que ya tiene la app hoy (Dab, Shooting, Dormir, Salir). Una interfaz visual de "Memory Manager" queda como mejora futura si hace falta.

### Resultado esperado

El usuario puede ver qué recuerda Cognimon, borrarlo todo, sacar una copia, y apagar la memoria sin tocar código ni archivos a mano (salvo que quiera editar el export).

------------------------------------------------------------------------

## 5. Mapa de archivos

| Archivo | Cambio |
|---|---|
| `memory/db.py` | **Nuevo.** Esquema y conexión SQLite por personaje. |
| `memory/manager.py` | **Nuevo.** `MemoryManager`: remember/recall/forget/update/summarize/consolidate/score + export_json/import_json. |
| `memory/analyzer.py` | **Nuevo.** Prompt y parseo del "Memory Analyzer" (Fase 2). |
| `ai/context_builder.py` | **Nuevo.** Arma el payload final (system + memorias + historial + mensaje). |
| `ai/prompt.py` | `system_prompt()` acepta bloque de memorias relevantes. |
| `ai/ollama_client.py` | Historial de corto plazo interno; soporte para embeddings (`/api/embeddings`). |
| `ui/desktop.py` | Instancia `MemoryManager`; llama al Context Builder antes de responder; dispara el Memory Analyzer después; agrega submenú de memoria. |
| `.gitignore` | Agregar `data/`. |
| `data/<character>/memory.db`, `data/<character>/conversations/*.jsonl` | **Nuevo en runtime** (no versionado). |

No hace falta tocar `character/cognimon.py`, `character/curimon.py` ni la máquina de estados — la memoria vive entre `ui/desktop.py` y `ai/*`, igual que en el plan anterior.

------------------------------------------------------------------------

## 6. Definition of Done (adaptado del propio `etapa_2.md`)

**Core**
- [ ] `MemoryManager` implementado con las 7 operaciones.
- [ ] SQLite para datos estructurados (identidad + memorias + embeddings).
- [ ] Búsqueda semántica funcionando sobre esos embeddings.
- [ ] Identidad única por Digimind, persistente entre sesiones.

**Memoria**
- [ ] Short-term, long-term, episodic y semantic memory, los cuatro tipos.
- [ ] Importance score y recency influyen en qué se recupera.
- [ ] Consolidación agrupa memorias relacionadas.
- [ ] Contradicciones actualizan en vez de duplicar.

**Integración con LLM**
- [ ] Retrieval corre antes de generar cada respuesta.
- [ ] Context Builder arma el payload final.
- [ ] Memory extraction corre después de cada conversación.
- [ ] Nunca se manda toda la memoria al LLM (siempre top-K).

**Usuario**
- [ ] Ver memorias.
- [ ] Eliminar memorias / borrar todo.
- [ ] Exportar / importar.
- [ ] Desactivar memoria.

------------------------------------------------------------------------

## 7. Fuera de alcance de esta etapa

- **UI gráfica de "Memory Manager"** (el mockup con recuadros del documento) — se resuelve con el menú contextual existente por ahora.
- **Conexión memoria → personalidad/Evolution** — el propio documento la marca como algo que "conecta posteriormente con Evolution" (Etapa 7); esta etapa solo deja los datos listos para que Etapa 3/7 los consuman.
- **Vector DB dedicado** (Chroma/FAISS) — se usa SQLite + NumPy como se explicó en la sección 2; migrar es un cambio contenido si hace falta más adelante.
- **Digital Core completo** (personalidad, evolución, relaciones) — Etapa 1; acá solo se construye la identidad mínima que memoria necesita.
