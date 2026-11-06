# Estado y resultados del timing

Corte actualizado: 5 de noviembre de 2026, 23:50, hora de Córdoba. Los resultados de octubre mantienen su fecha histórica. Plataforma KR260, K26 `xck26-sfvc784-2LV-c`, Vivado 2026.1, top `kr260_top`. El proyecto de Vivado conserva el nombre `ariane_kr260_debug`. La campaña analizada usa `cv64a6_imafdc_sv39`; el README general del repositorio describe también otras configuraciones y no reemplaza el manifiesto de cada corrida.

## Resultados del 4 de noviembre

| Variante y objetivo | Resultado | WNS ns | TNS ns | Setup negativos |
|---|---|---:|---:|---:|
| CAST2 0/1/1 a 100 MHz | Implementación final sin cierre | −0,239 | −109,091 | 1030 |
| CAST3 1/1/1 a 100 MHz | Cierre STA final, hardware pendiente | 0,000 | 0,000 | 0 |
| CAST3 1/1/1 a 100 MHz, implementación nueva con PS en IOPLL/10 | Implementación final sin cierre | −0,208 | −90,293 | 1014 |
| CAST3 1/1/1 a 120 MHz | Implementación final sin cierre | −1,806 | −10.882,976 | 18.654 |

CAST3 a 100 MHz terminó a las 14:50. Setup y hold cumplen con márgenes que redondean a 0,000 ns; pulso +3,500 ns, cuatro restricciones de bus skew cumplidas y ruteo completo sin errores. La variante agrega un ciclo de conversión respecto de CAST2. Las poblaciones finales difieren y esta comparación no demuestra idéntico rendimiento por ciclo.

La implementación nueva tiene el mismo RTL, las mismas estrategias y el mismo checksum de síntesis que el cierre, pero cambia la configuración del PS y la colocación resultó peor. Con margen 0,000 ns, unos 0,2 ns alcanzan para no cerrar; el resultado equivale a unos 98 MHz. Esto no invalida el cierre de CAST3. Ver [por qué dieron distinto](comparacion_implementaciones_100mhz_20261104.md). A 120 MHz, el resultado final reemplaza la estimación de síntesis de WNS −2,088 ns.

Ver [paquete y resultados finales](actualizacion_20261105_paquete_100mhz.md), [comparación, reportes y recuperaciones hasta las 16:53:58](actualizacion_20261104_cast.md) y métricas con hashes del [4 de noviembre](auditorias/timings_20261104.json) y del [5 de noviembre](auditorias/timings_20261105.json).

### Paquete de 100 MHz

Del checkpoint de CAST3 que cerró salieron bitstream, sondas, XSA y FSBL, sin reimplementar. El reloj de PL0 lo programa el FSBL, con IOPLL/10 y 99,999 MHz. Al reabrir el checkpoint se repitieron 0,000 ns de setup y hold a 10 ns. El FSBL compiló con el parche de reset y, frente al de 90,9 MHz, solo cambia en el divisor de PL0 y la fecha de compilación.

**La prueba en placa de este paquete está pendiente.** `cva6 ensayo --frecuencia 100` ya lo usa, pero no se ejecutó con hardware. Esa prueba tampoco ejercita la FPU.

## Cierre a 90,9 MHz del 22 de octubre

| Métrica final | Resultado |
|---|---:|
| PL0 configurado | 90,908180 MHz, IOPLL / 11 |
| Período de análisis | 11,000 ns |
| WNS / TNS de setup | +0,001 / 0,000 ns |
| Endpoints de setup con violaciones | 0 de 96.451 |
| WHS / THS de hold | +0,004 / 0,000 ns |
| Endpoints de hold con violaciones | 0 de 96.435 |
| WPWS / TPWS | +4,000 / 0,000 ns |
| Redes ruteables completamente ruteadas | 88.351 de 88.351 |
| Errores de ruteo | 0 |
| Bus skew | 4 restricciones MET, mínimo +9,535 ns |

Fuente primaria: [timing final AggressiveExplore](../../../timing-preparation/pl0_91mhz_20261022/reports_aggressive/timing_summary.rpt), [resumen](../../../timing-preparation/pl0_91mhz_20261022/reports_aggressive/summary.txt), [ruteo](../../../timing-preparation/pl0_91mhz_20261022/reports_aggressive/route_status.rpt). El reporte analiza Slow y Fast para retardos máximos y mínimos. El DRC conserva advertencias y no enumera errores ni critical warnings; no describirlo como un diseño sin warnings.

La secuencia fue síntesis `Vivado Synthesis Defaults`, implementación `Performance_ExploreWithRemap`, route `NoTimingRelaxation -tns_cleanup` y phys_opt post-route `Explore`. Esa corrida terminó con **WNS −0,065 ns, TNS −4,311 ns y 147 endpoints**. Una pasada adicional **`phys_opt_design -directive AggressiveExplore`** produjo el cierre. Ver [Tcl de implementación](../../../timing-preparation/pl0_91mhz_20261022/run_impl_91mhz.tcl) y [Tcl de optimización final](../../../timing-preparation/pl0_91mhz_20261022/aggressive_physopt.tcl).

El margen de setup es 1 ps al redondeo del reporte. Es un resultado positivo de STA de ese checkpoint; no garantiza que todas las futuras implementaciones cierren ni reemplaza una prueba funcional.

### Paquete que debe conservarse

[timing_closed_91mhz_2026-10-22](../../corev_apu/fpga/software/kr260_ps_boot/timing_closed_91mhz_2026-10-22/README.md) contiene BIT, LTX, XSA, DCP, reportes, scripts, estado del proyecto y `SHA256SUMS.txt`. **El `impl_1` del proyecto conserva el resultado anterior negativo; su bitstream no es el bitstream cerrado.** El XSA cerrado se exportó desde el checkpoint final en modo no-proyecto para incluir el resultado correcto. Mantener juntos los artefactos y verificar su manifiesto antes de transferirlos o usarlos. En esta consolidación se comprobaron **29/29 archivos**, sin faltantes ni diferencias. El DCP `kr260_top_91mhz_closed.dcp` tiene SHA256 `26e20f4b961718b5e12b8e0e676db6b5268a6831e3c3a4985ba7fe63bbe13df4`.

La prueba en placa de este paquete está **pendiente**. El último paquete documentado como conocido bueno en hardware es [known_good_2026-09-18](../../corev_apu/fpga/software/kr260_ps_boot/known_good_2026-09-18/README.md), a 25 MHz. Allí se documentó PASS de BootROM y escrituras DDR observadas por ILA; ese alcance no equivale a una validación exhaustiva de ISA, Linux o toda la memoria.

### Preparación del arranque a 90,9 MHz

El 29/10 se generó y compiló el FSBL91 en una salida nueva, `operacion/cva6_ops/fsbl91/build_20261029_1831`, usando el XSA cerrado de 91 MHz, IOPLL/11 y el parche de reset. El [manifiesto](../../../operacion/cva6_ops/fsbl91/build_20261029_1831/fsbl91_manifest.json) registra **PASS de compilación**, `build_only=true`, `hardware_validated=false` y `reset_hold_verified=true`. El [ELF preparado](../../../operacion/cva6_ops/fsbl91/build_20261029_1831/kr260_fsbl_91mhz_patched.elf) tiene SHA256 `4b2c98d7ea93099d62b7538ce4d92b071d3672ef157b48acf7bf688df380ab87`. Los paquetes congelados de 25/91 MHz permanecieron intactos.

Los scripts de arranque JTAG y capturas están preparados en la [guía de automatización](../../../automatizacion/README.md). Falta comprobarlos con la placa y registrar PASS/FAIL e ILA; ni el build del FSBL ni los planes generados reemplazan esa validación. La reproducción del FSBL es opcional y debe usar una salida nueva. El [plan de BootROM original y programas DDR](plan_bootrom_original_y_programas_ddr.md) es documental y no se aplicó al CPU ni a la ROM actuales.

## Resultados históricos a 100 MHz hasta el 29 de octubre

| Referencia física | WNS ns | TNS ns | Endpoints negativos | WHS ns | Uso |
|---|---:|---:|---:|---:|---|
| Gold dirigido histórico | −0,553 | −434,730 | 1716 | +0,003 | Referencia anterior preservada |
| Base FMA145 | −0,553 | −363,606 | 1439 | +0,003 | Base de la última tanda nocturna |
| SATP009 | −0,553 | −322,607 | 1285 | +0,003 | Mejor adoptado de la etapa histórica y recargado |
| Composición FMA010 | −0,553 | −322,047 | 1282 | +0,003 | Válida; no adoptada por la regla de medias |

Autoridad para la última selección: [summary.json de la noche](../../../timing-preparation/focused_physical_20261021/night_run_20261021/summary.json). La pasada SATP009 mejoró TNS **40,999 ns**, aproximadamente **11,28 %**, y quitó **154 endpoints negativos** respecto de FMA145. El peor camino no mejoró, por lo tanto no se cerró setup.

La composición FMA010 tuvo un TNS algo menor pero redujo la media de slack de la población fija completa en unos 0,00000896 ns. El controlador aplicó una regla estricta de no regresión y conservó SATP009. “Análisis válido”, “aceptado por el analizador” y “adoptado como mejor” no son el mismo estado.

### Límite de frecuencia y período

La estimación usada en la investigación fue `Tmin ≈ T − WNS`, para los caminos de ciclo completo comparables del checkpoint. A partir de SATP009: `10 − (−0,553) = 10,553 ns`, equivalente a **94,76 MHz estimados**. Esto no demuestra cierre con un nuevo ruteo a 94,76 MHz ni ejecución en placa. El paquete cerrado de 90,9 MHz tiene otra ubicación y otro ruteo.

La cifra **88,18 MHz** de `frequency_audit/routed_initial_estimate.json` pertenece al estado intermedio a 11 ns con WNS −0,340 ns, antes de las optimizaciones finales. Quedó superada por el cierre posterior. La investigación exhaustiva automatizada de períodos no llegó a ejecutarse por completo: el recolector está preparado, pero faltan sus salidas y su revisión final. Conservar esta diferencia entre estimación, prueba STA y prueba en placa.

## Ensayo histórico de retiming del 22 de octubre

[exp100_retiming_20261022](../../../timing-preparation/exp100_retiming_20261022/exp100_retiming.tcl) ensayó síntesis con retiming en runs separados `synth_2` / `impl_2`, sin cambios de RTL del CPU. El intento final terminó el 22 de octubre a las 16:15:42, sin errores de síntesis y con **0 movimientos en los 50 resúmenes por módulo**. El script abortó ese último intento antes de implementación. Un intento anterior sí inició implementación y fue interrumpido; otros registran problemas de RAM/swap. No hay cierre post-route nuevo proveniente del último intento.

La estimación de síntesis reportó slack global/PMP −0,145 ns, CAST/FPU +0,053 ns, operandos +0,301 ns y SATP +2,651 ns. Esos valores son diagnósticos pre-route. El log también menciona restricciones por múltiples relojes en registros no movibles; el resultado de cero retiming no demuestra una única causa ni agota todas las variantes.

## Próximas verificaciones del corte histórico del 29 de octubre

1. Verificar los hashes del paquete cerrado de 90,9 MHz y del FSBL91 ya compilado; ejecutar el flujo de placa preparado y registrar PASS/FAIL e ILA, después de repetir la referencia conocida de 25 MHz.
2. Completar el análisis de período mínimo/frecuencia máxima con los checkpoints finales, separando dominios de clock, tipos de camino y frecuencia realmente programada por el PS.
3. Si continúa la búsqueda de 100 MHz, formular una hipótesis nueva que actúe sobre los grupos críticos compartidos y conservar SATP009 como referencia. El historial no justifica repetir a ciegas las mismas recetas ni afirmar imposibilidad universal.
4. Definir una ventana nueva y recuperar margen de disco antes de otra campaña. Estas tareas documentadas no fueron lanzadas en esta consolidación.

## Próximos pasos al 5 de noviembre

1. Repetir la referencia de 25 MHz y correr `cva6 ensayo --frecuencia 100 --con-ila --ejecutar`; registrar PASS/FAIL e ILA.
2. Ampliar las comprobaciones funcionales con el procesador completo, contemplando el ciclo adicional de conversión y la corrección de extensión de signo.
3. Usar los caminos finales de la prueba de 120 MHz si se busca otra optimización. La discusión sobre 150 MHz fue conceptual y no produjo una corrida.
