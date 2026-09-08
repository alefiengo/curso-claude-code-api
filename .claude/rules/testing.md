# Reglas de testing

## Reproducir antes de corregir

- Ante cualquier fallo reportado, se reproduce primero con un caso real
  contra el sistema: un test que se ejecuta y falla en rojo, o una ejecución
  real (por ejemplo, contra la API corriendo) que deja evidencia concreta
  del fallo — código de estado, mensaje de error, salida de un comando.
- La corrección se escribe después de tener esa reproducción, nunca antes.
- La corrección no oculta la reproducción: el test o la evidencia que probó
  el fallo se queda tal como se escribió. No se debilita, no se borra y no
  se reescribe para esconder lo que reprodujo.
