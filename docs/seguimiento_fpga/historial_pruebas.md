# Historial de las pruebas de timing

La tabla de métricas y recetas a 100 MHz está en [evaluaciones_100mhz.csv](evaluaciones_100mhz.csv): 48 registros históricos, tres implementaciones finales del 4 de noviembre y una del 6 de noviembre. La [entrada CAST2/CAST3](actualizacion_20261104_cast.md) reúne la comparación por etapa y la [entrada del 5 de noviembre](actualizacion_20261105_paquete_100mhz.md) los resultados finales posteriores. Los registros de síntesis, otras frecuencias, intentos rechazados, interrupciones y comprobaciones se conservan por separado en [la auditoría histórica](auditorias/historico.json).

## Cobertura y forma de contar

La revisión identificó **36 carpetas de resultados generales completados a 100 MHz**, más **5 candidatos físicos diurnos y 7 nocturnos** de la etapa focalizada. El corte histórico contiene esos 48 registros con métricas; la actualización del 4 de noviembre añade las dos variantes finales a 100 MHz, la implementación nueva con el PS en IOPLL/10 lleva el total a 51, y la de la ROM mínima del 6 de noviembre a 52. Las recargas de comprobación, importaciones y copias del mismo resultado no se presentan como optimizaciones nuevas. Un resultado con timing negativo es utilizable para comparar y sigue siendo un fallo de cierre.

No es un conteo de todas las opciones posibles de Vivado ni de toda la historia oral del proyecto. Las primeras mediciones mencionadas a 150 y 300 MHz no se reconstruyen numéricamente sin un artefacto identificable; las listas de clocks planificadas no prueban que esos ensayos hayan terminado. La revisión local sí encontró un resultado final a **125 MHz**, Defaults/current, WNS **−3,139 ns**, TNS **−32642,748 ns** y WHS **+0,002 ns**, además de un intento Carry/125 interrumpido. Sus fuentes están en el JSON histórico.

## Evolución histórica de las campañas hasta el 29 de octubre

| Etapa | Qué se hizo | Resultado o aprendizaje |
|---|---|---|
| Piloto y matriz inicial | Síntesis actual y Defaults; combinaciones de implementación | Primer post-route −1,294 ns; Defaults/current mejoró a −0,665 ns |
| Variantes generales | Carry, AlternateRoutability y directivas de placement/route/phys_opt | No cerraron a 100 MHz |
| Replicación SATP y ajustes dirigidos | Réplicas y optimización física con netlist conservada | SATP solo −0,566 ns; combinado −0,558 ns; post-route adicional llegó a −0,553 ns |
| Recetas ML concretas | Variantes registradas de las recomendaciones de Vivado | Mejor de esas recetas −0,609 ns; no superó el gold −0,553 ns |
| Cribado de síntesis | RESOURCE_SHARING off, AreaOptimized_high y NO_LC | Comparación estimada; fue necesario implementar para evaluar el resultado real |
| NoSharing y NO_LC implementadas | Comparación con la base de implementación | NoSharing −1,853 ns; NO_LC −1,201 ns. La aparente mejora pre-route no se sostuvo |
| Implementaciones dirigidas y floorplanning | Reruteo, clocks, optimización posterior y ubicación de grupos | Ninguna superó el WNS −0,553 ns; varias empeoraron |
| Censo del 21/10 | Peor camino por endpoint negativo, drivers y conexiones comunes | Grupos compartidos detectados; un muestreo top-N no cubre todos los caminos |
| Reruteo local CAST | Rama auto_delay, objetivo350ps y red completa shortest-delay | auto_delay empeoró a −0,617 ns; las otras variantes no mejoraron |
| Grupos físicos diurnos | SATP y FMA sobre la mejor netlist | FMA145 conservó WNS −0,553 ns y bajó TNS a −363,606 ns |
| Noche del 21/22 | Restruct/pin/ECO por familias y composiciones | SATP009 adoptado: −0,553 / −322,607 ns,1285 endpoints |
| Día pasivo del 22/10 | Continuación limitada por recursos | Interrumpida en baseline por RAM; cero candidatos físicos nuevos válidos |
| Build91MHz del 22/10 | Clock PS coherente, implementación y AggressiveExplore adicional | Cierre STA +0,001 ns; paquete congelado, hardware pendiente |
| Retiming100MHz del 22/10 | Síntesis separada con retiming y varios intentos | Último intento0movimientos; no implementación final nueva |
| Investigación del 25–28/10 | PDF y comparación con fuentes externas | Análisis y contexto; no son nuevas corridas locales |

## Políticas de síntesis registradas

La auditoría identificó perfiles con implementación completada: configuración actual del proyecto, `Vivado Synthesis Defaults`, `Flow_PerfThresholdCarry`, `Flow_AlternateRoutability`, Defaults con `RESOURCE_SHARING=off` y Defaults con `NO_LC=true`. `Flow_AreaOptimized_high` quedó como cribado de síntesis; su estimación fue claramente peor. El ensayo posterior de retiming es una rama separada. Esto describe variantes efectivamente registradas, no todo el espacio de parámetros.

| Cribado de síntesis100MHz | WNS estimado ns | TNS estimado ns | Alcance |
|---|---:|---:|---|
| no_share | -0.396 | -29.962 | Estimación post-síntesis; implementación separada |
| area_high | -3.547 | -8325.468 | Estimación post-síntesis; implementación separada |
| no_lc | -0.397 | -37.697 | Estimación post-síntesis; implementación separada |


La receta de implementación de referencia usa opt `ExploreWithRemap`, place `Explore`, phys_opt `Explore`, route `NoTimingRelaxation -tns_cleanup` y post-route `Explore`. Los ajustes dirigidos y la pasada adicional AggressiveExplore se registran como pasos propios sobre un checkpoint concreto; no confundir esa secuencia con un único preset universalmente ganador.

## Detalle de la noche histórica del 21 y 22 de octubre

Ventana prevista: 21/10 23:01:18 a22/10 08:01:18, con cierre de búsqueda a06:31:18. Terminó antes, cerca de03:31:54, al consumir la cola/cupos de composiciones de esa versión. Quedó tiempo sin usar; no fue una exploración exhaustiva.

Los **10 intentos revisados** se reparten en **7 candidatos válidos**, **2 fallos de automatización antes de optimización física** y **1 rechazo de integridad después de ejecutar optimización física**. Otras **2 interrupciones previas** y **2 recargas noop** se registran aparte.

| Candidato válido nocturno | WNS ns | TNS ns | Endpoints negativos | Adoptado |
|---|---:|---:|---:|---|
| 002_restruct_CAST | -0.553 | -363.606 | 1439 | No |
| 004_pin_CAST | -0.553 | -363.606 | 1439 | No |
| 006_restruct_FMA | -0.553 | -363.046 | 1436 | No |
| 007_restruct_FMA_TNS | -0.553 | -352.106 | 1432 | Sí |
| 008_restruct_FMA | -0.553 | -351.546 | 1429 | No |
| 009_restruct_SATP | -0.553 | -322.607 | 1285 | Sí |
| 010_restruct_FMA | -0.553 | -322.047 | 1282 | No |


Las fallas iniciales de CAST se debieron a consultas Tcl/API incorrectas; se conservaron y corrigieron en versiones posteriores. No prueban que la política física hubiera empeorado el timing. Los ECO previstos se omitieron al encontrar bloqueos de ruteo reales; tampoco cuentan como estrategias ejecutadas sin mejora.

PMP005 sí ejecutó optimización física y produjo un resultado parcial. Se rechazó por **11 cambios de controles RAMB36E2:8ENBWREN y3WEBWE**, sin una justificación de equivalencia que permitiera aceptarlos bajo la regla aplicada. Sus slacks provisionales no entran en la tabla de candidatos válidos ni en la selección de ganadores. Ver `integrity_rejection_005_pmp` y las rutas primarias en la auditoría histórica.

El `skipped` heredado del estado menciona ASID8/10; es texto histórico y no describe el SATP009 ejecutado, cuya cohorte usa ASID15. Para las recetas reales usar los `job_target`, análisis y reportes del ensayo, no sólo esa etiqueta.

## Referencias de identidad

| Artefacto | SHA256 registrado o verificado |
|---|---|
| [SATP009 final.dcp](../../../archivo/timing-preparation/focused_physical_20261021/night_run_20261021/runs/009_restruct_SATP/final.dcp) | `169be1450fd1881259ecebe4401790971fe770310a469cc6ef1ff0b0431494ce` |
| [DCP cerrado91MHz](../../corev_apu/fpga/software/kr260_ps_boot/timing_closed_91mhz_2026-10-22/kr260_top_91mhz_closed.dcp) | `26e20f4b961718b5e12b8e0e676db6b5268a6831e3c3a4985ba7fe63bbe13df4` |


Los hashes históricos de100MHz se conservan como evidencia de sus manifiestos; no se reabrieron esos DCP en Vivado durante esta consolidación. El paquete91MHz sí se verificó completo contra su manifiesto: **29/29 archivos,0faltantes,0diferencias**. Las tablas y los informes no reemplazan los archivos originales.

## Campaña CAST del 4 de noviembre

| Variante a 100 MHz | Reparto entrada/interior/salida | WNS síntesis ns | WNS ruteado antes de Explore ns | WNS final ns | TNS final ns | Setup negativos finales |
|---|---|---:|---:|---:|---:|---:|
| CAST2 | 0/1/1 | −0,421 | −0,423 | −0,239 | −109,091 | 1030 |
| CAST3 | 1/1/1 | −0,421 | −0,101 | 0,000 | 0,000 | 0 |
| CAST3, implementación nueva con PS en IOPLL/10 | 1/1/1 | −0,415 | −0,580 | −0,208 | −90,293 | 1014 |

CAST3 cerró STA a 100 MHz con margen prácticamente nulo y un ciclo adicional de conversión. El resultado de tres registros pertenece a su copia privada identificada; desde el 6 de noviembre el repositorio también usa `LAT_CONV=3` (commit `9c333f3fe`). Los errores del controlador después de route se recuperaron desde los DCP completos, sin contar las recuperaciones como nuevas síntesis.

La prueba posterior de CAST3 a 120 MHz se lanzó a las 15:23 con recursos limitados. Su síntesis estimó WNS −2,088 ns, TNS −2059,825 ns y 1845 endpoints de setup negativos. Terminó a las 19:19 sin cierre, con WNS −1,806 ns, TNS −10.882,976 ns y 18.654 endpoints de setup negativos. Esos valores se registran en `resultados_clave.csv`; no se agregan a la tabla de implementaciones finales de 100 MHz.

La implementación nueva con el PS en IOPLL/10 empezó a las 19:19 y terminó a las 20:52 sin cierre, incluso con `AggressiveExplore`. No se adoptó. El [paquete de 100 MHz](actualizacion_20261105_paquete_100mhz.md) salió del checkpoint de CAST3 que cerró, y la [comparación de implementaciones](comparacion_implementaciones_100mhz_20261104.md) explica la diferencia.

Ver [registro completo y fuentes](actualizacion_20261104_cast.md). Los resultados de octubre describen otras netlists y el alcance anterior sin cambios de RTL. Se conservan como antecedentes; el nuevo cierre no debe presentarse como otra receta física sobre el mismo checkpoint histórico.

## Prueba en placa del 6 de noviembre

Este diseño cerró timing esa madrugada, con incremental desde CAST3: WNS/TNS 0,000/0,000 ns y WHS +0,006 ns.

| Corrida | Secuencia | Resultado |
|---|---|---|
| Intento previo | FSBL, FPGA y FSBL otra vez, con un FSBL cortado | El FSBL se colgó en el entrenamiento de la DDR (`80C000FF`) y no se soltó el CVA6 |
| Primera | FSBL, FPGA y FSBL otra vez, sin cortar y con Vivado desconectado hasta terminar | PASS |
| Segunda | FPGA y un solo FSBL | PASS |

Ver [registro de la prueba](actualizacion_20261106_prueba_placa_ddr.md).
