---
name: segmentar-commits
description: >-
  Reparte los cambios pendientes del repositorio (working tree o stage) en
  commits de una sola intención cada uno, en un orden que deja el repositorio
  en un estado comprobable después de cada commit. Usa Conventional Commits,
  elige el prefijo según lo que hace el commit, no según el tipo de archivo, y
  muestra el reparto propuesto esperando aprobación explícita antes de tocar
  git. Úsala cuando el usuario pida repartir cambios en commits, cerrar una
  sesión de trabajo en commits separados, o dividir un diff grande en commits
  atómicos.
---

# Segmentar cambios en commits

Esta skill propone un reparto de commits y, solo tras aprobación explícita,
los crea. No reescribe historia ni decide por su cuenta sin mostrar el reparto
antes.

## Fase 1 — Estado real del repositorio

Antes de proponer nada, ejecuta:

```bash
git status --short
git diff --stat
git diff --stat --cached
```

Este es el mapa del cambio: qué archivos cambiaron y cuánto, no su contenido.
No leas el diff completo (`git diff` sin `--stat`, `git show`, abrir archivos
enteros) todavía — el reparto se decide primero a nivel de archivo con este
mapa. Nunca asumas el estado del repositorio a partir de lo hablado antes en
la conversación: vuelve a consultarlo aquí, en el momento de invocar la skill.

Solo si el mapa no alcanza —un archivo mezcla con claridad más de una
intención y hace falta un corte más fino que el archivo completo— lee el
diff de ese archivo puntual (`git diff -- <archivo>`) para ubicar los hunks
o funciones que corresponden a cada commit. No lo hagas para archivos cuyo
cambio completo ya pertenece a una sola intención.

## Fase 2 — Diseño del reparto

Reglas para dividir:

- **Una intención por commit.** Un commit es un cambio de comportamiento
  coherente: una capacidad, un arreglo, una tarea de mantenimiento. No mezcles
  una capacidad nueva con un arreglo a algo que ya existía, aunque toquen el
  mismo archivo.
- **Orden verificable.** Cada commit, aplicado hasta ahí, debe dejar el
  repositorio en un estado que se pueda comprobar con los comandos canónicos
  del proyecto (`uv run pytest -q`, `uv run ruff check .`, y cuando aplique
  `uv run alembic upgrade head` / `downgrade base`, ver `README.md` /
  `CLAUDE.md`). En la práctica esto casi siempre ordena así: esquema o
  migración antes que el código que lo usa; cambios a un fixture de test antes
  que los tests que dependen de él; una capacidad antes que su documentación.
- **Prefijo por intención, no por archivo.** El tipo de Conventional Commits
  (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `build`, `ci`, `perf`,
  `style`) lo decide lo que el commit hace observable, no dónde vive el
  archivo. Un commit que añade una capacidad es `feat` aunque incluya su
  migración y sus tests. Un commit que solo corrige un test existente por una
  fragilidad expuesta por otro cambio es `fix`, aunque el archivo sea de
  tests. Un commit que solo toca `docs/` es `docs`.
- **Staging parcial solo si hace falta.** Un archivo se reparte entre varios
  commits únicamente cuando de verdad mezcla más de una intención. Si el
  archivo completo pertenece a un solo commit, no lo fracciones. El reparto
  parcial se hace siempre con `git add -p` sobre el cambio que ya existe en
  el árbol de trabajo — nunca editando el archivo.

## Fase 3 — Propuesta y espera

Muestra el reparto propuesto, un bloque por commit, en el orden en que se
comitearían:

- Número y una frase de la intención.
- Los archivos completos que entran; si hay staging parcial, qué partes
  (funciones, clases, hunks) de qué archivo.
- El mensaje completo, en Conventional Commits, siguiendo el estilo de
  `git log` de este repositorio (asunto en minúscula tras el prefijo, cuerpo
  en imperativo cuando el porqué no sea obvio).

No ejecutes `git add` ni `git commit` en esta fase. Espera aprobación
explícita del usuario. Si el usuario pide cambios al reparto, ajústalo y
vuelve a mostrarlo antes de continuar.

## Fase 4 — Ejecución (solo tras aprobación)

Para cada commit aprobado, en el orden propuesto:

1. Deja en stage exactamente lo propuesto, siempre a partir del cambio que
   ya existe en el árbol de trabajo:
   - Archivo completo: `git add <archivo>`.
   - Parte de un archivo: `git add -p <archivo>`, aceptando o rechazando
     hunks. Si un hunk mezcla líneas de más de un commit, no lo aceptes
     entero: usa la opción `e` (editar manualmente) de `git add -p` para
     dejar en el hunk que se comitea solo las líneas de esta intención,
     conservando las demás para un commit posterior.
   - Archivo nuevo que hay que repartir entre varios commits:
     `git add -N <archivo>` primero (lo deja rastreado sin contenido en el
     índice), y recién ahí `git add -p <archivo>` como con cualquier otro.
   - Nunca uses Edit/Write ni ninguna otra vía para modificar el contenido
     del archivo en el árbol de trabajo con el fin de simular un estado
     intermedio: el archivo en disco no se toca en ningún momento de esta
     fase; todo el reparto ocurre en el índice.
2. `git diff --cached --stat` para confirmar que el stage coincide con lo
   propuesto antes de comitear.
3. Corre la comprobación canónica que aplique a ese commit.
4. Si falla: detente, no comitees ese paso ni sigas con los siguientes,
   informa qué falló.
5. Si pasa: `git commit` con el mensaje ya mostrado y aprobado.

## Fuera de alcance

- No reescribe historia (`rebase`, `amend`) ni combina con commits ya
  existentes.
- No reescribe código para armar un commit. Cada commit sale exclusivamente
  de `git add` (completo o `-p`, con edición manual de hunks cuando haga
  falta) sobre el cambio que ya existe en el árbol de trabajo. El contenido
  de los archivos en disco no se toca en ningún momento de la Fase 4.
- No decide el reparto sin mostrarlo antes ni comitea sin aprobación
  explícita, commit por commit.
- No inventa contenido: el reparto sale de lo que `git status` / `git diff`
  muestran en el momento de invocarla, no de lo hablado antes en la
  conversación.
- No abre `.env`.
