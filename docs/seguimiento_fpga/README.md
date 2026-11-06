# Documentación unificada del CVA6 en KR260

Actualizada el 6 de noviembre de 2026; los resultados de timing tienen corte el 5 de noviembre a las 23:50, hora de Córdoba. Este es el punto de entrada para el proyecto FPGA, las campañas de timing y su recuperación. Los informes originales conservan su fecha y alcance; el estado vigente se resume aquí.

**Resultado vigente:** CAST3 cerró STA a **100 MHz** el 4 de noviembre a las 14:50, con **WNS/TNS y WHS/THS 0,000/0,000 ns**, cero endpoints negativos y margen prácticamente nulo al redondeo. De ese checkpoint salió el [paquete de 100 MHz](actualizacion_20261105_paquete_100mhz.md), con bitstream, XSA y FSBL a 99,999 MHz, **todavía sin ejecutar en placa**. CAST2 quedó en WNS −0,239 ns y TNS −109,091 ns. **Una implementación nueva de CAST3 con el PS en IOPLL/10 terminó en WNS −0,208 ns y CAST3 a 120 MHz en −1,806 ns; ninguna cerró.** La [comparación fechada](actualizacion_20261104_cast.md) identifica etapas, fuentes y alcance funcional hasta su corte, y la [comparación de implementaciones](comparacion_implementaciones_100mhz_20261104.md) explica por qué dos corridas de CAST3 dieron distinto.

El paquete del 22 de octubre conserva el cierre a **90,908180 MHz configurados en el PS**, análisis a 11 ns, WNS +0,001 ns y WHS +0,004 ns. El cierre de CAST3 y la prueba de 120 MHz conservan el clock físico del PS de unos 90,9 MHz en sus proyectos; el reloj de 100 MHz lo aplica el FSBL del paquete nuevo. El último estado documentado como validado en hardware sigue siendo 25 MHz.

**Preparación para placa:** el FSBL91 se compiló con **PASS de software** desde el XSA cerrado, IOPLL/11 y el parche de reset, en `build_20261029_1831`: [manifiesto](../../../operacion/cva6_ops/fsbl91/build_20261029_1831/fsbl91_manifest.json) y [ELF](../../../operacion/cva6_ops/fsbl91/build_20261029_1831/kr260_fsbl_91mhz_patched.elf). Los scripts JTAG/captura están preparados en la [guía de automatización](../../../automatizacion/README.md); falta ejecutarlos con la placa. El [plan de BootROM original y programas DDR](plan_bootrom_original_y_programas_ddr.md) describe trabajo futuro y no modifica el CPU ni la ROM actual.

El FSBL de 100 MHz también tiene **PASS de compilación** y `cva6 ensayo --frecuencia 100` ya usa ese paquete. Ni ese flujo ni el de 90,9 MHz se ejecutaron todavía con la placa.

## Estado del repositorio

Al 6 de noviembre, CAST3 y el reloj de 100 MHz ya están en commits de la rama `feature/kr260-ddr4-integration`. La rama está subida a `origin` (`ignaciofalchini/CVA6`, público). Para subir hay que usar la cuenta `ignaciofalchini`, porque la activa en esta computadora, `nachofalchi`, no tiene permiso de escritura.

| Commit | Contenido |
|---|---|
| `9c333f3fe` | `fpnew_cast_multi.sv`, `LAT_CONV=3` y `fp_cvt.opLat = 3` en gem5 |
| `793c70103` | PL0 a IOPLL/10 en el BD y `.xpr` sin los restos del experimento de retiming |
| `de0381410` | Aplicación ARM, parche de reset del FSBL, scripts y tests |

La documentación se versiona en el commit siguiente, y desde entonces git registra sus cambios; los hashes del 5 de noviembre conservan ese corte.

Quedan fuera de git, a propósito, `reports/`, los binarios de los paquetes de `kr260_ps_boot`, los `archivo_documental_*.tar.gz` y `corev_apu/ariane_kr260_ps_bd_backup.tcl`. También quedan fuera `automatizacion/` y `Automatizacion-FPU-100MHz/`, donde están el DCP cerrado y el paquete de 100 MHz.

El repositorio no reproduce por sí solo el cierre: otra implementación del mismo RTL dio WNS −0,208 ns, y la referencia sigue siendo el DCP cerrado. En un clon nuevo, el wrapper del BD no existe porque se genera; se crea con `corev_apu/fpga/scripts/prepare_kr260_ddr.tcl`. En un clon se comprobó que el proyecto abre sin fuentes faltantes, con PL0 a 100 MHz, y que genera el mismo `psu_init.c` del paquete. No se completó ni elaboración ni síntesis desde un clon.

## Rutas reales

Entrar al [repositorio](../..), al [proyecto Vivado](../../corev_apu/fpga/ariane_kr260_debug/ariane_kr260_debug.xpr), a los [archivos de placa](../../corev_apu/fpga/software/kr260_ps_boot), a la [entrega](../../../entregas/reunion_profesor_20261030) o a la [automatización](../../../automatizacion). Se retiró el menú de accesos directos. Los dos logs citados por documentación volvieron como archivos reales a su ubicación original en el HOME; los otros 18 permanecen archivados.

## Reunión del 30 de octubre de 2026

[Resumen para la reunión](reunion_20261030/RESUMEN_REUNION.md), [PDF y evidencia para compartir](../../../entregas/reunion_profesor_20261030/README_ENTREGA.md) y [respaldo local verificable](../../../backups/reunion_20261030/README_RECUPERACION.md).

El corte documental comprimido de las 00:13 del 29/10 se conserva sin cambios. La preparación posterior de la reunión y la limpieza de caché están registradas por separado; su inventario histórico no se presenta como un escaneo posterior a esa limpieza.

## Respaldo externo verificado

El respaldo esencial se copió el 29/10 a OpenClawd y pasó verificación SHA256 de los 50 archivos. [Recibo y ubicación](../../../RESPALDO_EXTERNO_20261029.md). Los archivos para la placa siguen locales; [guía para trabajar con Gonza](../../../PARA_PLACA_CON_GONZA_20261030.md).

## Guía de lectura

| Consulta | Documento |
|---|---|
| Paquete de 100 MHz, prueba en placa y resultado final de 120 MHz | [Registro del 5 de noviembre](actualizacion_20261105_paquete_100mhz.md) |
| Por qué dos implementaciones de CAST3 a 100 MHz dieron distinto | [Comparación de implementaciones](comparacion_implementaciones_100mhz_20261104.md) |
| Pruebas CAST2/CAST3 a 100 MHz e inicio de 120 MHz | [Registro del 4 de noviembre](actualizacion_20261104_cast.md) |
| Qué se consiguió, qué significa y qué falta | [Estado y resultados](estado_y_resultados.md) |
| Campañas, mejores combinaciones y pruebas descartadas | [Historial de pruebas](historial_pruebas.md) |
| Restricciones, métricas y criterios de aceptación | [Metodología y decisiones](metodologia_y_decisiones.md) |
| Logout, reinicio, recursos, pausas y recuperación | [Operación y recuperación](operacion_y_recuperacion.md) |
| Arquitectura, reportes, investigación y documentación histórica | [Mapa documental](mapa_documental.md) |
| Qué afirmaciones antiguas necesitan contexto o corrección | [Aclaraciones documentales](aclaraciones_documentales.md) |

## Datos y conservación

- [Resultados principales en CSV](resultados_clave.csv), [51 evaluaciones a 100 MHz](evaluaciones_100mhz.csv) y [registro de decisiones](decisiones.csv).
- [Fuentes documentales con SHA256](fuentes_documentales.json) y [inventario de archivos del trabajo](inventario_archivos.jsonl.gz).
- [Copia comprimida de documentación y evidencia compacta](archivo_documental_20261029.tar.gz); [alcance y exclusiones](alcance_archivo.json).
- [Auditorías de fuentes](auditorias) y [verificación de esta consolidación](validacion.json).
- [Hashes del corte histórico del 29 de octubre](SHA256SUMS.txt).
- [Evidencia de métricas del 4 de noviembre](auditorias/timings_20261104.json), [hashes de los archivos actualizados](SHA256SUMS_20261104.txt) y [archivo documental nuevo](archivo_documental_20261104_cast.tar.gz).
- [Evidencia del 5 de noviembre](auditorias/timings_20261105.json), [sus hashes](SHA256SUMS_20261105.txt) y [su archivo documental](archivo_documental_20261105_100mhz.tar.gz).

Los reportes completos, censos, DCP, bitstreams y demás artefactos grandes siguen en sus ubicaciones originales, identificados por el inventario y los manifiestos de cada campaña. La copia comprimida preserva documentación, scripts y evidencia de tamaño acotado; no contiene todos los productos de Vivado. El respaldo esencial seleccionado ya tiene una copia externa verificada en OpenClawd; los resultados y archivos para la placa permanecen locales. El inventario documental anterior conserva su fecha de corte.

## Alcance vigente

El alcance histórico hasta el 29 de octubre conservaba RTL, parámetros y microarquitectura. La campaña del 4 de noviembre incorpora el cambio de registros de CAST del viernes y la variante `LAT_CONV=3` autorizada por el usuario, con reparto 1/1/1 y un ciclo adicional de conversión. Ese alcance específico no habilita otros cambios en PMP, TLB, cachés o pipeline del procesador. El objetivo inmediato es probar en placa el paquete de 100 MHz y conservar el cierre STA de CAST3 como referencia.

La revisión operativa del 29 de octubre y las ventanas de campañas anteriores son registros históricos. Al corte actual no hay campañas activas. Las guías de la [prueba de 120 MHz](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/README-120MHz.md) y de la [implementación con el reloj real](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/README-100MHz-real.md) quedan como referencia.

Para continuar el registro, agregar una fila a `decisiones.csv` y a `resultados_clave.csv` cuando corresponda, enlazar el reporte final y actualizar este resumen. Conservar las fuentes originales y generar un archivo documental nuevo con fecha propia al hacer otro corte.
