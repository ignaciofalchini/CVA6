# CVA6 en KR260 - Estado para la reunión del 30 de octubre de 2026

Preparado el 29/10/2026. Vivado 2026.1, K26 xck26-sfvc784-2LV-c, top kr260_top, configuración cv64a6_imafdc_sv39. Se mantiene el CVA6 existente, sin cambiar su RTL, parámetros, pipeline ni latencias.

## Mensaje para abrir la reunión

Tenemos el CVA6 integrado con la DDR del PS y una prueba funcional conocida a 25 MHz. Conseguimos cerrar el timing a 90,908 MHz y guardamos un paquete coherente con bitstream, probes ILA, XSA, checkpoint y reportes. El FSBL91 ya se compiló desde ese XSA, con IOPLL/11 y el parche de reset, y los scripts JTAG/captura están preparados. Ese PASS es de software: falta probarlos con la placa. A 100 MHz hicimos una búsqueda amplia de políticas y optimizaciones físicas: mejoró la cantidad y la suma de las violaciones, pero el peor camino sigue fuera de tiempo. El resultado actual es cierre STA a 90,9 MHz; todavía no es una validación en placa a esa frecuencia.

## Qué tenemos y qué falta

| Hito | Estado | Evidencia |
|---|---|---|
| CVA6 y DDR alta del PS, 25 MHz | Validación funcional documentada | BootROM PASS e ILA de escrituras, known_good_2026-09-18 |
| Diseño físico a 90,908180 MHz | Timing cerrado | WNS +0,001 ns, TNS 0, WHS +0,004 ns, pulso +4 ns |
| BIT, LTX, XSA y DCP de 90,9 MHz | Generados y congelados | 29/29 hashes correctos; payload del BIT coincide con XSA |
| FSBL91 y scripts de arranque/captura | Preparados; compilación PASS | build_20261029_1831: XSA91, IOPLL/11 y parche de reset; sin prueba de hardware |
| Arranque a 90,9 MHz en placa | Pendiente | Falta ejecutar el flujo preparado y registrar PASS/FAIL e ILA |
| Implementación a 100 MHz | No cierra setup | WNS -0,553 ns, TNS -322,607 ns,1285 endpoints negativos |
| Documentación y resultados | Consolidados | 48 evaluaciones100 MHz con métricas, recetas y fuentes; planes y resúmenes |

El margen de setup a 90,9 MHz es1 ps: cumple el reporte final, pero no ofrece holgura para asumir que cualquier nueva corrida cerrará. Permanecen 75 pines excluidos por clock constante del DMI-JTAG inactivo; están identificados, coinciden con la referencia y no se confunden con el BSCAN de ILA/VIO.

## Qué aprendimos de las pruebas

La tabla contiene 36 resultados generales y 12 candidatos físicos posteriores; no son 48 síntesis e implementaciones completas independientes. Se reutilizaron síntesis y checkpoints para aislar el efecto de cada política. Los ensayos interrumpidos, errores de automatización y candidatos rechazados por integridad están clasificados aparte.

A100 MHz la receta general de síntesis Defaults más implementación de referencia llegó a WNS -0,665 ns. Las réplicas dirigidas y optimizaciones post-route llevaron el mejor WNS a -0,553 ns. Sobre ese nivel, las optimizaciones por grupos redujeron TNS de -434,730 a -322,607 ns:25,79 % menos magnitud y 431 endpoints negativos menos (1716 a 1285), sin mejorar el WNS.

Hay familias distintas cerca del límite: conversión FPU (CAST), FMA, protección de memoria (PMP), caché, MMU y operandos. Muchos destinos comparten tramos de lógica y ruteo. Corregir un grupo puede reducir el problema global sin mover el peor camino de otro grupo. La NoSharing que parecía algo mejor en síntesis terminó peor implementada (-1,853 ns); NO_LC también empeoró (-1,201 ns). La síntesis por sí sola no decide el cierre final.

La noche física terminó con SATP009 como resultado adoptado. FMA010 bajó ligeramente más el TNS (-322,047 ns), pero el controlador no la adoptó por una pequeña regresión en la media de una población fija completa. El ensayo posterior de retiming en síntesis movió0 registros en los 50 resúmenes por módulo; el intento final no produjo implementación nueva.

## Archivos que deben distinguirse

- **Paquete correcto90,9 MHz:** corev_apu/fpga/software/kr260_ps_boot/timing_closed_91mhz_2026-10-22/. Contiene el BIT cerrado, LTX, XSA y DCP. El BIT de impl_1 quedó en -0,065ns y no es el mismo resultado.
- **FSBL91 nuevo, fuera del paquete congelado:** operacion/cva6_ops/fsbl91/build_20261029_1831/. [Manifiesto de compilación](/home/nachofalchi/data/fpga-work/operacion/cva6_ops/fsbl91/build_20261029_1831/fsbl91_manifest.json) y [ELF91](/home/nachofalchi/data/fpga-work/operacion/cva6_ops/fsbl91/build_20261029_1831/kr260_fsbl_91mhz_patched.elf), SHA256 `4b2c98d7ea93099d62b7538ce4d92b071d3672ef157b48acf7bf688df380ab87`. Build de software verificado; hardware pendiente.
- **Referencia funcional25 MHz:** corev_apu/fpga/software/kr260_ps_boot/known_good_2026-09-18/. El XSA25 correspondiente está fuera, en hardware/kr260_cva6.xsa.
- **Mejor adoptado100 MHz:** timing-preparation/focused_physical_20261021/night_run_20261021/runs/009_restruct_SATP/final.dcp.
- **Proyecto editable:** corev_apu/fpga/ariane_kr260_debug/ariane_kr260_debug.xpr. El repositorio está en feature/kr260-ddr4-integration; existen cambios locales y archivos no versionados que el respaldo debe incluir.

Los 17 artefactos del paquete25 MHz coinciden con sus hashes históricos. La única discrepancia de su SHA256SUMS es la entrada del propio manifiesto (autorreferencia); se conserva como registro histórico y se genera un manifiesto externo para la copia nueva.

## Orden y conservación

La documentación central está en docs/seguimiento_fpga/README.md. Se conservan reportes, planes, scripts, fuentes y conclusiones con fecha. Los archivos grandes siguen en sus rutas originales. La copia documental anterior de 16 MB es un archivo de documentación, no un respaldo completo de los binarios.

El 29/10 se eliminaron 649 archivos de cuatro directorios de caché/scratch regenerables, unos 441 MiB. Se guardaron 134 diagnósticos de texto y se revalidaron los checkpoints protegidos. No se eliminaron experimentos ni reportes únicos. Después se consolidaron 106 copias idénticas entre 143 reportes históricos: todas sus rutas y bytes se conservan, las copias compartidas quedan de sólo lectura y sus fechas/modos originales se pueden recuperar desde un archivo verificado. El ahorro de duplicados es 1,095 GiB, además de unos 96 MiB de temporales adicionales.

El respaldo esencial verificado ya está en OpenClawd, en `nacho@192.168.86.31:/home/nacho/backups/CVA6/reunion_20261030`: 50 archivos y 774.762.195 bytes comprobados por SHA256. Incluye bundles Git, cambios locales, archivos nuevos y artefactos seleccionados; no es una imagen completa del disco ni de todas las campañas. Los archivos para la placa siguen locales. También se respaldaron los clones temporales de investigación antes de retirarlos y se eliminó un instalador prescindible de caché: esa última limpieza liberó unos 2,8 GiB y dejó unos 6,3 GiB libres.

## Próximos pasos y decisiones para conversar

1. Verificar los hashes del FSBL91 ya compilado y revisar los planes de la [automatización](/home/nachofalchi/data/fpga-work/automatizacion/README.md), sin modificar el CPU ni los paquetes congelados. Regenerar el FSBL sólo si se necesita reproducir el build, en una salida nueva.
2. Repetir primero la referencia de 25 MHz y después ejecutar la prueba de 90,9 MHz: comprobar PASS en STATUS0=0x800004000 y guardar resultados/capturas con la identidad de BIT/LTX/FSBL/XSA. La aplicación ARM actual escribe en DDR; no es un cargador genérico.
3. Acordar si90,9 MHz es la base suficiente para el trabajo y cuánto esfuerzo adicional merece100 MHz.
4. Si continúa 100 MHz, usar hipótesis físicas concretas sobre los grupos críticos y una ventana acotada, manteniendo siempre el mejor resultado anterior. No prometer cierre por probar más presets.
5. Conservar el respaldo externo verificado y decidir el archivado de ensayos antiguos después de revisar su valor como evidencia.

## Qué podemos afirmar

El reporte final de90,9 MHz cumple setup/hold/pulso bajo las restricciones documentadas; el paquete está íntegro. Tenemos una prueba DDR funcional previa a25 MHz y evidencia amplia de optimización sin modificar el CPU. No está demostrado el funcionamiento de90,9 MHz en placa, no cerramos100 MHz y tampoco demostramos su imposibilidad universal. Los94,76 MHz calculados desde el WNS del checkpoint100 MHz son una estimación, no otra frecuencia validada. Las frecuencias publicadas por otros ports sólo son comparables si coinciden CPU, FPU, memoria, dispositivo y tipo de evidencia.

## Fuentes de consulta

Base de rutas: /home/nachofalchi/data/fpga-work.

- docs/seguimiento_fpga/estado_y_resultados.md e historial_pruebas.md, dentro de cva6-equipo.
- timing-preparation/pl0_91mhz_20261022/reports_aggressive/: reporte final de cierre91 MHz.
- timing-preparation/focused_physical_20261021/night_run_20261021/summary.json y reportes de009/010.
- Paquetes known_good_2026-09-18 y timing_closed_91mhz_2026-10-22, con sus README y manifiestos.
- [Manifiesto FSBL91](/home/nachofalchi/data/fpga-work/operacion/cva6_ops/fsbl91/build_20261029_1831/fsbl91_manifest.json), [guía de automatización](/home/nachofalchi/data/fpga-work/automatizacion/README.md) y [plan de BootROM original y programas DDR](/home/nachofalchi/data/fpga-work/cva6-equipo/docs/seguimiento_fpga/plan_bootrom_original_y_programas_ddr.md). Este último es un plan documental; no se aplicaron cambios a la ROM ni al CPU.
- Timing_CVA6_KR260.pdf (25/10), con las aclaraciones del índice central; investigación comparativa del 27 y 28/10.
