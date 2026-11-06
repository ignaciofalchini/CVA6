# Timing de CAST con dos y tres registros a 100 y 120 MHz

Corte: **4 de noviembre de 2026, 16:53:58, hora de Córdoba**. Plataforma KR260,
K26 `xck26-sfvc784-2LV-c`, Vivado 2026.1, top `kr260_top`.

**CAST3 cerró el análisis final a 100 MHz; CAST2 quedó con WNS −0,239 ns.**
La prueba de CAST3 a 120 MHz continúa en implementación. Su síntesis muestra
WNS −2,088 ns y todavía no tiene resultado final ruteado.

## Cambio de registros y alcance funcional

El cambio del viernes 30 de octubre está en `fpnew_cast_multi.sv`, la unidad de
conversiones de la FPU. Con `DISTRIBUTED` y dos registros, el reparto
entrada/interior/salida pasó de **1/1/0 a 0/1/1**. La latencia de conversión
conserva dos ciclos. En la variante de tres registros, `LAT_CONV=3` produce
**1/1/1** y agrega un ciclo de latencia a las conversiones.

Se revisaron datos, estado, etiquetas, máscara y señales auxiliares junto con
ready/valid y flush. Las dos variantes pasaron la simulación focalizada de CAST,
con 23 vectores dirigidos, estímulos aleatorios y pruebas de stalls, reset y
flush. Esa prueba cubre el bloque de conversiones; la integración completa del
procesador y la validación en placa siguen pendientes. El ciclo adicional debe
considerarse al comparar rendimiento y al actualizar el modelo correspondiente.

Las corridas usan copias privadas de las fuentes. El paquete del repositorio
original conserva `LAT_CONV=2`; el cierre de CAST3 identifica su propia copia
congelada. A 120 MHz se reutiliza el mismo RTL y reparto de CAST3 de 100 MHz.

## Comparación por etapa

Todos los márgenes están en ns. Los puntos negativos son endpoints con al menos
una violación, no una enumeración de todos los caminos combinatorios posibles.

| Objetivo y variante | Etapa | WNS | TNS | Setup negativos | WHS | Hold negativos |
|---|---|---:|---:|---:|---:|---:|
| 100 MHz CAST2 | Síntesis estimada | −0,421 | −36,999 | 292 | −0,033 | 8276 |
| 100 MHz CAST2 | Ruteo antes de pasada final | −0,423 | −312,456 | 1447 | +0,010 | 0 |
| 100 MHz CAST2 | Final con Explore | −0,239 | −109,091 | 1030 | +0,004 | 0 |
| 100 MHz CAST3 | Síntesis estimada | −0,421 | −36,999 | 292 | −0,033 | 8342 |
| 100 MHz CAST3 | Ruteo antes de pasada final | −0,101 | −14,427 | 311 | +0,007 | 0 |
| 100 MHz CAST3 | Final con Explore | **0,000** | **0,000** | **0** | **0,000** | **0** |
| 120 MHz CAST3 | Síntesis estimada | −2,088 | −2059,825 | 1845 | −0,033 | 8342 |
| 120 MHz CAST3 | Implementación final | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |

Fuentes y hashes por fila: [evidencia del corte](auditorias/timings_20261104.json).
Las estimaciones de síntesis de 100 MHz se reconstruyeron desde las corridas
completas, con el proyecto enlazado abierto en modo de solo lectura y objetivo
de 10 ns. La prueba de 120 MHz exporta el reporte durante el flujo, antes de
implementar. La reconstrucción de reportes no cuenta como otra síntesis.

La comparación final CAST2/CAST3 mejora WNS en **0,239 ns** y elimina los
1030 endpoints de setup negativos de CAST2. Las poblaciones finales tienen
96.348 y 96.648 endpoints de setup, respectivamente: son implementaciones
distintas y no corresponde tratar sus distribuciones como una población fija.

## Cierre confirmado de CAST3 a 100 MHz

La pasada final terminó a las **14:50:13 del 4 de noviembre**. El reporte final
indica `All user specified timing constraints are met.` con período de 10 ns.
WNS/TNS y WHS/THS son 0,000/0,000 ns, con cero endpoints negativos de setup y
hold. El margen de pulso es +3,500 ns, sin violaciones. Las 88.125 redes
ruteables están completamente ruteadas y no hay errores de ruteo.

Las cuatro restricciones de bus skew cumplen, con margen mínimo +9,478 ns.
DRC y metodología conservan advertencias; no se identificaron errores ni
advertencias críticas en sus resúmenes. Se revisó el conjunto exacto de 75 pines
del DMI-JTAG inactivo sin restricción por reloj constante. Hay cero endpoints
activos sin restricción. Esa condición se mantiene documentada y no se
introdujeron excepciones nuevas para obtener el cierre.

**El margen reportado es prácticamente nulo:** setup y hold redondean a
0,000 ns con precisión de 1 ps. El resultado acredita esta implementación a
100 MHz y no demuestra margen para aumentar su frecuencia.

El checkpoint ganador es
[CAST3 final.dcp](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/recuperacion_20261104/cast3/reports/final.dcp),
SHA256 `4c7dadcac240b21a39a95c4d05d8b75e30ec60f06724ed731e8895a94025edae`.
El [manifiesto ganador](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/recuperacion_20261104/cast3/reports/winner_manifest.json)
identifica RTL, reportes y checkpoint.

## Violaciones en síntesis y cierre en implementación

La síntesis construyó la netlist correctamente y su análisis estimado tenía
violaciones de setup y hold. Antes de la colocación y el ruteo, Vivado estima
los retardos de las conexiones. La implementación determina las ubicaciones y
rutas físicas, además de transformar lógica y optimizar conexiones.

En CAST3 se midió directamente la mejora de la última pasada: empezó desde el
checkpoint ruteado con WNS −0,101 ns y TNS −14,427 ns y terminó en 0,000/0,000 ns.
El log registra 164 celdas o conexiones optimizadas, 45 intercambios de pines,
transformaciones lógicas y reubicaciones. Ver
[log de la pasada Explore](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/recuperacion_20261104/cast3/reports/finalize.console.log).

El peor camino de síntesis va de PMP `pmpaddr[3][3]` al write buffer de la
caché; el peor final usa otros bits de PMP y otro destino. La resta de sus
retardos no mide la mejora de un mismo camino. El cierre se establece con
el conjunto de comprobaciones del reporte final, manteniendo el objetivo de
10 ns. [Modelo de interconexión de Vivado, AMD UG906](https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/Interconnect).

## Prueba de 120 MHz con consumo limitado

Se inició a las **15:23:11** en una carpeta nueva, con servicio persistente
`cva6-fpu120-low-da6bd612efe94a7d.service`. La síntesis del top terminó a las
**16:13:43** y los reportes estimados se completaron a las **16:15:54**.
Al corte de las 16:53:58, la implementación sigue en optimización posterior a
la colocación (`Post Placement Timing Optimization`). Faltan las etapas
restantes, el ruteo y la pasada final Explore con sus reportes.

El objetivo es 8,333333333 ns; Vivado lo cuantiza a **8,333 ns** y el semiperíodo
a 4,167 ns. Por ese redondeo el reporte muestra 120,005 MHz. El controlador
verifica el objetivo solicitado y la cuantización de 1 ps para evitar rechazar
un reloj correcto por su representación numérica.

El peor camino estimado conserva los mismos extremos PMP y el mismo retardo
de datos de 10,154 ns que en síntesis a 100 MHz. El período disponible baja
aproximadamente 1,667 ns y el WNS pasa de −0,421 a **−2,088 ns**. Este déficit
equivale a cerca del 25 % del período de 120 MHz. Es una dificultad considerable,
pero el veredicto de cierre queda pendiente del análisis final ruteado.

El presupuesto aplicado a todos los procesos del servicio es un hilo de Vivado,
un job a la vez, máximo agregado de un núcleo de CPU, `nice 15`, prioridad de
disco idle, regulación desde 4 GiB de memoria y máximo de 5 GiB de RAM más
5 GiB de swap. CPU y memoria se comprobaron en el cgroup efectivo. El peso de
I/O solicitado no está expuesto por el kernel de este servicio; la prioridad
de disco comprobada es `ionice idle` de sus procesos.

A las 16:30 se observaron aproximadamente 3,2 GiB de RAM y 4,3 GiB de swap,
sin OOM ni errores de ejecución. Son medidas del sistema; el pico de memoria
que informa Vivado tiene otra definición. La utilización de swap y los límites
de CPU prolongan esta prueba, por lo que sus tiempos no se comparan directamente
con los de la corrida de 100 MHz que usó más hilos.

[Guía y controles de la prueba](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/README-120MHz.md),
[reporte de síntesis](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/prueba_120MHz_20261104_baja_carga/cast3/reports/post_synthesis/timing_summary.rpt)
y [estado por etapa](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/prueba_120MHz_20261104_baja_carga/cast3/reports/execution.json).

## Decisiones y recuperaciones

| Momento del 4 de noviembre | Acción y resultado |
|---|---|
| Noche, hasta 01:28 | CAST2 completó síntesis y ruteo. Un chequeo de estado general confundió una etapa parcial válida con fallo. CAST3 no se ejecutó durante la noche. |
| Hasta 09:24 | Se recuperó el DCP ruteado y se aplicó Explore. CAST2 mejoró, pero quedó en WNS −0,239 ns. Por instrucción del usuario se canceló entonces el fallback a CAST3. |
| Desde 13:13 | El usuario volvió a autorizar CAST3 y se ejecutó la variante 1/1/1. |
| 14:30 a 14:50 | CAST3 terminó el ruteo. `open_run` rechazó el estado parcial de implementación; se abrió directamente una copia verificada del DCP ruteado y se completó Explore. El cierre final quedó confirmado a las 14:50. |
| Desde 15:23 | El usuario autorizó CAST3 a 120 MHz con baja carga. Se congelaron las mismas fuentes en una salida independiente y se inició una síntesis e implementación nuevas. |

Las recuperaciones se cuentan como continuación de cada experimento, no como
nuevas síntesis o implementaciones completas. Los estados y scripts anteriores
se conservan para explicar las interrupciones.

Se evaluó conceptualmente subir a 150 MHz: exigiría un período de 6,667 ns,
aproximadamente 3,333 ns menos que a 100 MHz. Los caminos críticos abarcan PMP,
FMA, caché y control. No se lanzó una corrida a 150 MHz ni se midió un cierre
a esa frecuencia. La acción autorizada y en ejecución es 120 MHz.

## Alcance físico y próximo registro

Los objetivos de 100/120 MHz son de STA. Estas campañas conservaron el BD y la
configuración física del PS de unos 90,9 MHz; no generaron BIT/XSA ni programaron
la placa. El cierre a 100 MHz debe llevarse a una configuración física de reloj
coherente y validarse en hardware. Los paquetes históricos de 25/90,9 MHz se
mantienen como referencias separadas.

Al terminar 120 MHz, incorporar `result.json`, período observado, WNS/TNS,
WHS/THS, endpoints, pulso, restricciones, bus skew, ruteo y el hash de su DCP.
Reemplazar el estado pendiente en el registro y comparar los resultados finales
por etapa. Un error de herramienta o una interrupción por recursos debe quedar
identificado y no convertirse en un fallo de timing ni en un cierre.
