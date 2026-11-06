# Operación y recuperación de las campañas

## Estado al 5 de noviembre

No hay campañas activas. CAST3 a 120 MHz terminó a las 19:19 del 4 de noviembre y la implementación con el PS en IOPLL/10 a las 20:52, ambas sin cierre. Sus fuentes y controladores congelados están fuera del repositorio FPGA, en la carpeta privada de la campaña.

Los servicios `cva6-fpu120-low-da6bd612efe94a7d.service` y `cva6-fpu100-real.service` figuran como `failed` con `ExecMainStatus=3`. En estos controladores, ese código significa análisis válido sin cierre, no un error de ejecución: confirmarlo en `state.json`, donde el estado es `complete_without_closure`.

Las dos corridas se serializaron con un candado compartido porque no entran juntas en memoria. El servicio de 120 MHz usó un hilo/job, un núcleo como máximo y 5 GiB de RAM más 5 GiB de swap. La implementación de 100 MHz usó 2 hilos en síntesis y 4 en implementación, y arrancó cuando había al menos 9 GiB libres entre RAM y swap. Un OOM puede terminar Python y dejar `state.json` en `running`: comprobar siempre `ActiveState`, `Result`, `ExecMainStatus` y los eventos de memoria del servicio.

Las dos recuperaciones de 100 MHz y el cierre final de CAST3 están documentados en la [entrada fechada](actualizacion_20261104_cast.md). El paquete para placa, cómo probarlo y cómo regenerarlo están en la [entrada del 5 de noviembre](actualizacion_20261105_paquete_100mhz.md).

## Rutina operativa histórica del 29 de octubre por la tarde

La [automatización local](../../../automatizacion/README.md) incorpora `cva6 estado`, `verificar`, `preparar-manana`, `fsbl91`, `ensayo`, `placa`, `captura` y `respaldo`. No retoma campañas históricas de timing. JTAG y transferencia de respaldo requieren ejecución explícita; logout usa servicios de usuario. FSBL91 ya compilado; validación en placa pendiente. El [plan BootROM/DDR](plan_bootrom_original_y_programas_ddr.md) sólo documenta cambios futuros y no se ejecutó.

Las cifras y unidades de las secciones siguientes corresponden al corte histórico que se indica en ellas; consultar el servicio real para estado y espacio disponibles.

## Estado observado el 29 de octubre

La consulta de unidades de usuario `cva6*` no encontró servicios activos; tampoco se detectaron workers reales de Vivado o controladores de timing en la auditoría operativa. `Linger=yes`. El último arranque del sistema observado fue el 22 de octubre a las 14:41:26. Los estados de la mañana de ese día no describen procesos vivos hoy.

Disco disponible al corte operativo: **2.326.863.872 bytes, aproximadamente 2,17 GiB**. Es inferior incluso a la reserva de parada de 2,5 GiB de algunos guards históricos. No alcanza el umbral de arranque de las campañas recientes. El valor es una instantánea; volver a consultar antes de ejecutar. Ver [auditoría de operación](auditorias/operacion.json).

## Consulta del estado real

Estos comandos consultan; no lanzan pruebas:

```bash
systemctl --user list-units --all --no-pager 'cva6*'
loginctl show-user nachofalchi -p Linger
df -h /home/nachofalchi/data/fpga-work
free -h
```

Para una unidad identificada, revisar `systemctl --user status NOMBRE.service` y `journalctl --user -u NOMBRE.service`. Cruzar PID, hora de actualización y logs con `state.json`/`summary.json`; una etiqueta `running` antigua no prueba que exista una corrida activa. Los `CURRENT_*` y los nombres de servicio son referencias fechadas, no una autorización para retomarlos.

## Recuperación después de logout o reinicio

Los workers lanzados como servicios de usuario pueden continuar después del logout mientras su gestor siga vivo y `linger` esté habilitado. Esto no los protege de apagado, reinicio, suspensión, OOM ni falta de disco. Los servicios transitorios y sus límites no se recrean automáticamente al reiniciar la máquina.

1. Identificar campaña, código congelado, manifiesto, checkpoint de entrada y último resultado validado.
2. Consultar procesos y unidad reales. No lanzar un segundo worker ni borrar locks sólo porque exista un estado antiguo.
3. Revisar la última etapa: un DCP final y sus validaciones permiten reutilizar un resultado; un `.partial.dcp` o un log activo no equivalen a una operación terminada.
4. Un comando nativo de placement/route/phys_opt interrumpido no continúa desde su instrucción interna: se vuelve a ejecutar la etapa prevista desde un checkpoint válido, conservando el intento interrumpido.
5. Verificar fuentes, restricciones, hashes y recursos antes de una reanudación. Usar `--resume` sólo dentro de la ventana original y conforme al controlador de esa campaña.
6. Para una campaña vencida, preparar una ventana nueva y código/configuración versionados que reutilicen la evidencia verificada. No editar la fecha ni el manifiesto de una campaña histórica para hacerla pasar por la misma ejecución.

## Entradas históricas principales

| Flujo | Entrada | Situación al corte |
|---|---|---|
| Matriz de síntesis e implementación | [timing_matrix.py](../../corev_apu/fpga/scripts/timing_matrix.py) | Interfaz general; ver guía y configuración de la campaña concreta |
| Barrido de clocks | [timing_sweep_service.py](../../corev_apu/fpga/scripts/timing_sweep_service.py) | Interfaz histórica; no asumir equivalencia con el flujo físico posterior |
| Noche física V3 | [start_night_v3.sh](../../../archivo/timing-preparation/focused_physical_20261021/night_run_20261021/start_night_v3.sh) | Ventana vencida el 22/10 a las 08:01:18 |
| Día pasivo | [start_day.sh](../../../archivo/timing-preparation/focused_physical_20261021/passive_day_20261022/start_day.sh) | Ventana vencida el 22/10 a las 21:00 |
| Colector histórico de evidencia | [collector_provenance.json](../../../archivo/timing-evidence/20261018/collector_provenance.json) | Cubre piloto y búsqueda 100–300; no toda la campaña posterior |

Las recetas exactas, servicios, `guard`, límites, pausa y reanudación se registran en [auditoría operativa](auditorias/operacion.json), los directorios de campaña y las guías [timing_matrix.md](../timing_matrix.md) / [timing_sweep.md](../timing_sweep.md). Son instrucciones con fecha: revisar valores actuales antes de ejecutar un comando de arranque. En particular, `--check` puede aprobar la estructura de una campaña aunque su ventana haya vencido; no certifica que esté lista para arrancar.

## Recursos y pausa

La tanda pasiva del 22/10 limitaba CPU a aproximadamente un núcleo lógico, dos threads de Vivado, prioridad baja, RAM máxima de 5 GiB y swap de 1 GiB. Su guard la detuvo durante el baseline por presión de memoria del host; ese intento no constituye una estrategia física fallida. El waiter esperaba recursos antes de un único resume y también tenía plazo absoluto. Ambos estados quedaron históricos después del reinicio.

Más RAM libre no obliga a Vivado a usarla: muchas fases dependen de secuencias y paralelismo limitado. Antes de aumentar CPU/threads, considerar la RAM y swap máximas observadas, el uso interactivo y el espacio temporal. No extrapolar tiempos de una pasada post-route al costo de síntesis más implementación completa.

Para una pausa prevista, usar el mecanismo de pausa entre etapas del controlador que esté efectivamente activo; comprobar que el supervisor detuvo la admisión de otra prueba. Si hay presión crítica, el guard puede cortar la tarea activa y guardar la causa. Conservar logs e intento parcial, y no registrarlo como resultado final.

## Espacio, compresión y copias

El inventario central registra tamaños y ubicaciones. Antes de una nueva campaña, revisar temporales regenerables y reportes fríos con las herramientas de archivo ya documentadas; no borrar gold, manifiestos, fuentes congeladas, paquetes conocidos buenos ni el resultado cerrado. La compresión de texto suele ser útil; DCP, BIT y XSA ya contienen datos comprimidos y su ahorro debe medirse.

[timing-evidence.md](../timing_evidence.md) describe el archivo por contenido `objects/<sha256>` y cómo recuperar versiones usando su índice. El último estado revisado de ese colector es del 19/10 y sus fuentes configuradas son el piloto y la búsqueda inicial; no afirmar que protege automáticamente las campañas del 21/22.

La copia `archivo_documental_20261029.tar.gz` usa el mismo criterio de identidad por SHA para documentación compacta. Para recuperar una fuente, localizar su ruta en `fuentes_documentales.json`, extraer el miembro `objects/SHA` indicado a una carpeta nueva y comprobar su hash antes de restaurarlo. El archivo también contiene `index.json`. No extraer encima de los originales para consultar.

La copia está en el mismo disco que el trabajo. Para protección frente a pérdida del disco, copiar documentación **y** paquetes/checkpoints seleccionados a otro destino y verificar hashes allí. No se configuró ni se realizó esa transferencia en esta tarea. No importar scripts de mantenimiento sólo para inspeccionarlos: `archive_cold_logs.py` tiene efectos de escritura al ejecutarse/importarse. Los 424 registros históricos de compresión corresponden a212 reportes únicos, no a424 experimentos.
