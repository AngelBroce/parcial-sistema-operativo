# Mini Administrador de Tareas (Tkinter) - Round Robin

Simulador simple de planificación de procesos con interfaz tipo Administrador de Tareas usando Tkinter. Implementa estados: Nuevo, Listo, Ejecución, Bloqueado, Zombi y Finalizado. Planificador Round Robin con quantum configurable, bloqueo/desbloqueo, finalización manual, y automatizaciones opcionales.

## Requisitos
- Python 3.10+ (recomendado 3.11)
- Tkinter (incluido en instalaciones estándar de Python para Windows)

## Ejecutar
Desde Windows (cmd):

```
python "app.py"
```

Si el comando `python` no abre Python 3.x, pruebe con:

```
py -3 "app.py"
```

## Controles principales
- Iniciar/Pausar CPU: inicia o detiene el bucle de ticks.
- Quantum: tamaño de rebanada para Round Robin.
- Velocidad: milisegundos por tick.
- Crear Proceso / Crear 5: añade procesos (opción "Automatizado" para permitir bloqueos aleatorios).
- Admitir a Listo: mueve procesos de "Nuevo" a "Listo" (si "Auto-admisión" está activo, se hace solo).
- Mantener mínimo 5: si hay menos de 5 procesos vivos, se crean automáticamente para cumplir el requisito.
- Bloquear/Desbloquear: simula E/S. El bloqueo agrega "tiempo de bloqueo" (ticks).
- Finalizar: termina procesos en ejecución o listos.
- Forzar Ejecución: sube un proceso listo a la cabeza de la cola RR.
- Bloqueos aleatorios: aplica bloqueos esporádicos al proceso en CPU si es "Automatizado".
- Auto-recolección Zombi / Recolectar Zombis: convierte procesos Zombi a Finalizado automáticamente o bajo demanda.

## Estados y colores
- Nuevo: azul claro
- Listo: verde claro
- Ejecución: amarillo claro
- Bloqueado: rojo claro
- Zombi: lila
- Finalizado: gris

## Notas de diseño
- Al agotar su ráfaga, un proceso pasa a estado Zombi y luego puede ser recolectado a Finalizado (automática o manualmente), emulando el comportamiento de procesos hijos que esperan `wait()`.
- El planificador usa una cola de listos FIFO y expira por quantum.
- La UI usa `after()` para simular ticks sin bloquear el hilo principal.

## Ideas creativas incluidas
- Estado Zombi y recolección.
- Modo automatizado con bloqueos aleatorios.
- Colores por estado.

## Problemas comunes
- Si no se ve la ventana, verifique que Python tenga Tkinter instalado.
- En equipos con múltiples versiones de Python, use `py -3`.
