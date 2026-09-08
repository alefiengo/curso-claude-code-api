# Reglas de estilo de código

## No reescribir código para armar commits

- Ninguna automatización de este proyecto que reparta o reorganice cambios
  ya existentes en el árbol de trabajo (por ejemplo, la skill
  `segmentar-commits`) reescribe código para simular un estado intermedio.
- El reparto se arma exclusivamente con `git add`, completo o con
  `git add -p` (incluida la edición manual de un hunk cuando mezcle más de
  una intención), sobre el cambio que ya existe en el árbol de trabajo.
- El contenido de los archivos en disco no se toca para conseguir ese
  reparto: lo que queda en cada commit sale del índice, nunca de una edición
  temporal del archivo.
