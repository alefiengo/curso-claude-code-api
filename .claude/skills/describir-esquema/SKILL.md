---
name: describir-esquema
description: >-
  Genera docs/esquema.md a partir del estado real de los modelos
  (app/models.py) y de alembic/versions/ en el momento de invocarla: un
  diagrama de las tablas y sus relaciones en Mermaid, y un diccionario de
  datos con una fila por columna. No repite docs/contrato-api.md, lo enlaza.
  Úsala cuando el usuario pida documentar, describir o diagramar el esquema
  de la base de datos, o refrescar docs/esquema.md tras un cambio de
  migraciones. Describe, no modifica.
---

# Describir el esquema de la base de datos

Esta skill produce **un solo documento**, `docs/esquema.md`. No toca modelos,
migraciones, el contrato ni la base de datos.

## Fase 1 — Estado real, no el supuesto

Antes de escribir una línea del documento, lee el estado actual del
repositorio en este orden. No trabajes de memoria ni de lo dicho antes en la
conversación: el esquema pudo cambiar.

1. **Los modelos.** `app/models.py` entero: cada clase que hereda de `Base`,
   su `__tablename__`, y cada `mapped_column` con su tipo, `nullable`,
   `unique`, `ForeignKey`, `primary_key` y `default`.
2. **La cadena de migraciones.** Lista `alembic/versions/*.py` y ordénala
   siguiendo `down_revision` de cada archivo, desde la que tiene
   `down_revision = None` hasta la cabeza. Para cada revisión, lee su
   `upgrade()`: qué tabla crea o altera, qué columnas, qué restricciones con
   nombre, y si tiene seed.
3. **El contrato.** `docs/contrato-api.md`, solo para saber qué ya está
   escrito ahí y debe enlazarse en vez de copiarse (ver Fase 3).

Si los modelos y las migraciones no concuerdan (una columna en `models.py`
que ninguna migración crea, o al revés), **no lo resuelvas**: anótalo en el
documento en una sección "Discrepancias detectadas" con el archivo y la línea
de cada lado, y sigue.

## Fase 2 — Contenido de `docs/esquema.md`

Un único archivo con dos partes y nada más.

### Parte 1 — Diagrama

Un diagrama entidad-relación en un bloque ```mermaid (`erDiagram`). Mermaid
porque es texto plano —se versiona y se diferencia línea a línea en un
commit— y GitHub lo renderiza solo en la vista del archivo, sin
herramientas.

- Una entidad por tabla, con sus columnas y tipos.
- Una relación por cada `ForeignKey`, con la cardinalidad que se lea de las
  restricciones (`nullable=False` en la FK => `||--o{`; nullable => `|o--o{`).
- Marca la clave primaria (`PK`) y las foráneas (`FK`).

### Parte 2 — Diccionario de datos

Una tabla Markdown por cada tabla de la base, con una fila por columna:

| Columna | Tipo | Nulos | Significado |
|---|---|---|---|

- **Tipo:** el tipo SQL como lo declara la migración (`INTEGER`,
  `VARCHAR(255)`, `TEXT`, `TIMESTAMP WITH TIME ZONE`), no el tipo de Python.
- **Nulos:** `sí` o `no`, de `nullable` en la migración.
- **Significado:** una frase, **solo cuando no es evidente por el nombre**.
  Para `id`, `name`, `title` no escribas nada. Para una columna de orden, una
  FK cuyo destino no es obvio, o un campo con una convención (un instante
  siempre en UTC, un entero sin rango), explica en una frase qué representa y
  de dónde sale su valor. Si el porqué ya está en `docs/contrato-api.md`,
  enlaza esa sección en vez de explicarlo.

Debajo de cada tabla, nombra las restricciones con nombre propio que crea la
migración (por ejemplo una `UNIQUE` nombrada) y las que dependen de ellas
(por ejemplo un seed con `ON CONFLICT`).

## Fase 3 — No repetir el contrato

`docs/esquema.md` describe la **forma de la base**: tablas, columnas, tipos,
nulos, relaciones, nombres de restricciones. Todo lo demás es del contrato y
se enlaza, no se copia:

- El comportamiento de los endpoints, los códigos HTTP, el orden de las
  colecciones, la normalización de texto: enlace a la sección de
  `docs/contrato-api.md`.
- El catálogo de estados y por qué llega por migración: ya está en la sección
  "Estados" del contrato; enlázala.
- La definición de "idempotente": enlace a `docs/glosario.md`.

Encabeza el documento con una frase que diga esto: "La forma de las tablas.
El comportamiento observable de la API está en
[docs/contrato-api.md](contrato-api.md)."

## Fase 4 — Mostrar antes de guardar

Muestra el `docs/esquema.md` completo en la respuesta y espera aprobación
explícita antes de escribir el archivo. Si `docs/esquema.md` ya existe, el
cambio se hace sobre él (es un refresco), mostrando qué cambia.

## Límite: describe, no modifica

Dentro de esta skill:

- No se edita `app/models.py`, ninguna migración de `alembic/versions/`,
  `docs/contrato-api.md` ni ningún otro archivo que no sea `docs/esquema.md`.
- No se crea ni se altera esquema: no se ejecuta `alembic revision`,
  `upgrade` ni `downgrade`.
- No se toca la base de datos: no se levanta PostgreSQL, no se consulta, no se
  ejecuta SQL. Todo lo que el documento afirma sale de leer `app/models.py` y
  `alembic/versions/`, no de introspeccionar una base viva.
- No se abre `.env`.

El único archivo que esta skill crea o modifica es `docs/esquema.md`.
