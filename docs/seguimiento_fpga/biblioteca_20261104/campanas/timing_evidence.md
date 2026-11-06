# Evidencias para presentar las pruebas de timing

Carpeta de consulta:
`/home/nachofalchi/data/fpga-work/timing-evidence/20261018/`

- `RESUMEN.txt`: explicación breve de los archivos y resultados disponibles.
- `timing_results.csv`: métricas finales por frecuencia, síntesis e implementación.
  El piloto reutilizado se muestra una sola vez, evitando duplicar un experimento.
- `synthesis_timing.csv`: métricas estimadas disponibles después de síntesis;
  identifica los reportes reconstruidos.
- `phase_times.csv`: tiempo real de ejecución, CPU y pico de memoria informado
  por Vivado para cada etapa, con el log de origen. El pico de Vivado no debe
  confundirse con una medida física de RAM del sistema.
- `index.json`: rutas originales y versiones históricas identificadas por SHA-256.
- `objects/<sha256>`: contenido archivado de cada versión. Los archivos idénticos
  comparten contenido; ninguna versión anterior se sobrescribe.
- `collector_provenance.json` y `collector_code/`: configuración y código del
  recolector para reproducir la preparación de las tablas.

El servicio `cva6-timing-evidence.service` revisa las dos corridas cada 60 segundos
con prioridad baja. Conserva fuentes congeladas, scripts, configuración, reportes,
logs, resultados, checkpoints, metadatos de recuperación y sus versiones cuando
cambian. Omite caches de Vivado, `.Xil` y archivos `.partial` todavía en escritura.
Los logs activos se guardan como snapshots, no como ejecuciones finalizadas.
Los archivos originales permanecen en las carpetas de las corridas.

El índice conserva las versiones ya archivadas aunque después desaparezca o se
sobrescriba el original. Para recuperar un archivo, buscar su ruta en `index.json`
y copiar `objects/<sha256>` al nombre deseado. Se probó conservación de versiones,
recuperación después de borrar el original y coincidencia del contenido con su hash.

Este archivo está en el **mismo disco** que los originales: protege el historial
frente a sobrescrituras, pero no sustituye una copia en otro disco o servidor.
No se configuró un destino externo porque no se indicó uno.

## Tiempo medido de la primera prueba

| Etapa | Duración de ejecución |
|---|---:|
| Síntesis del top CVA6 | 15 min 25 s |
| Espera de síntesis incluidas IPs previas | 19 min 47 s |
| Optimización lógica | 4 min 31 s |
| Placement | 15 min 08 s |
| Optimización física previa al routeo | 38 min 44 s |
| Routeo | 31 min 24 s |
| Optimización física posterior | 15 min 15 s |
| Checkpoints, reportes y resto del overhead de implementación | 2 min 34 s |
| **Implementación completa** | **1 h 47 min 36 s** |

Los 19 min 47 s incluyen los 15 min 25 s del top: **no sumarlos como dos tareas
independientes**. Los tiempos de etapa provienen de `elapsed` en los logs. El
intervalo de calendario incluye además la detención causada por el post-hook y
la recuperación; no corresponde a horas adicionales de cálculo de síntesis.
No se modifica la síntesis ni la implementación activa para generar las tablas.

## Reporte reconstruido de síntesis de 100 MHz

Se analizó la netlist enlazada guardada, con clock de 10 ns, usando
`report_synthesis_checkpoint.tcl`, sin repetir síntesis ni alterar el checkpoint.
Se ejecutó como servicio de baja prioridad `cva6-synth-timing-evidence.service`.

Origen de los reportes:
`/home/nachofalchi/data/fpga-work/timing-matrix/pilot_100mhz/recovery/synthesis_reconstructed/`

`provenance.json` identifica el checkpoint, su hash y el carácter reconstruido.
Se guardaron clocks, resumen min/max, 20 caminos críticos de setup, 20 de hold,
chequeos de restricciones y utilización jerárquica. Estos resultados **no son un
reporte emitido originalmente durante la primera síntesis**, ni cierre post-route.

| Métrica | Estimación post-síntesis reconstruida | Primera implementación post-route |
|---|---:|---:|
| WNS | −0,070 ns | −1,294 ns |
| TNS | −7,577 ns | −2169,251 ns |
| WHS | −0,033 ns | 0,000 ns |
| THS | −118,510 ns | 0,000 ns |

Los retardos de interconexión estimados después de síntesis cambiaron con el
placement y routeo. El setup estimado ya era ligeramente negativo; el margen
empeoró en la primera implementación. El hold se corrigió durante implementación.
Ninguno de esos resultados demuestra cierre a 100 MHz. Para comparar otras
estrategias se usarán los reportes finales, manteniendo los estimados como
información diagnóstica y conservando los chequeos de restricciones por separado.

El primer reporte post-route también enumera 75 extremos del JTAG sin restricción
por clock constante. El snapshot de `kr260_top.sv` conecta `tck_i` a cero. Esa
condición se conserva documentada; no se ocultó con excepciones nuevas. El
validador automático estricto exige revisar estos avisos antes de avanzar con un
resultado de slacks positivos.

Las próximas síntesis de la búsqueda activa ya tienen generación de
`synthesis_timing.rpt` y utilización después de enlazar las IPs, y el recolector
las analiza y archiva automáticamente. La versión del script del repositorio para
nuevas corridas amplía además esa salida a min/max, clocks, chequeos y caminos
críticos separados; las versiones congeladas del experimento activo no se
sustituyen en mitad de la ejecución.

La versión del runner del repositorio conserva reportes anteriores en
`report_history/` antes de regenerarlos. En la corrida activa, el archivo continuo
preserva adicionalmente los resultados que ya se producen.
