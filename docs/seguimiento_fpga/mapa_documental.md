# Mapa de documentación y evidencia

## Proyecto y versiones

| Referencia | Alcance |
|---|---|
| [Proyecto Vivado KR260](../../corev_apu/fpga/ariane_kr260_debug/ariane_kr260_debug.xpr) | Proyecto de trabajo; no sustituye los paquetes congelados |
| [Estado previo de Git](auditorias/estado_git_previo.json) | Commit, rama y modificaciones preexistentes al consolidar |
| [known_good del 18/09](../../corev_apu/fpga/software/kr260_ps_boot/known_good_2026-09-18/README.md) | Evidencia funcional DDR en placa a 25 MHz |
| [Paquete cerrado del 22/10](../../corev_apu/fpga/software/kr260_ps_boot/timing_closed_91mhz_2026-10-22/README.md) | Cierre STA a 90,9 MHz, placa pendiente |
| [Workspace inicial](../../../archivo/CVA6_VIVADO_WORKSPACE.md) | Historia de Genesys2 y configuración inicial de julio; no es el estado KR260 actual |

La arquitectura pasó por un port mínimo, debug con BRAM, prototipo DDR baja y luego integración DDR alta. No ejecutar restauraciones de una variante antigua sobre el proyecto actual sin revisar su alcance. La guía histórica de recuperación de septiembre describe BRAM y no reconstruye por sí sola el sistema DDR actual.

## Integración, memoria y depuración

| Documento original | Contenido y alcance |
|---|---|
| [Puertos KR260](../kr260_port_analysis.md) | Análisis inicial del port |
| [Camino de memoria](../kr260_memory_path.md) | Contexto del sistema de memoria |
| [BootROM de prueba](../kr260_bootrom_memory_test.md) | Prueba bare-metal y sus límites históricos |
| [Arquitectura PS DDR](../kr260_ps_ddr_architecture.md) | Prototipo inicial con DDR baja; no confundir con el mapeo posterior |
| [Integración DDR](../kr260_ddr_integration.md) | Ventana CVA6 `0x80000000..0xbfffffff` a DDR alta PS `0x800000000..0x83fffffff`; estado de septiembre |
| [ILA y VIO](../kr260_ila_vio.md) | Probes, resets y observaciones; las instrucciones BRAM están identificadas como históricas |
| [Lint KR260](../kr260_lint.md) | Chequeos y límites del lint |
| [Versionado y recuperación](../kr260_versionado_y_recuperacion.md) | Estado BRAM del 11/09, Git y Archive Project |
| [Retest FSBL del 07/10](../../corev_apu/fpga/software/kr260_ps_boot/retest_2026-10-07/README.md) | Software regenerado y compilado, pendiente de validación física en ese registro |

Informes previos: [port](../../reports/kr260_port/FINAL_REPORT.md), [siguientes pasos](../../reports/kr260_next_steps/FINAL_REPORT.md), [elaboración DDR del 17/09](../../reports/kr260_ddr_pre_synth/RESULTADO.md), [auditoría del 10/09](../../reports/kr260_audit_20260910.md) y [lint](../../reports/kr260_lint/FINAL_LINT_REPORT.md). El título “FINAL” sólo cierra el alcance de su tanda, no todo el proyecto.

## Timing y campañas

- [Guía de barrido](../timing_sweep.md), [matriz de políticas](../timing_matrix.md) y [evidencia](../timing_evidence.md).
- [timing-matrix](../../../archivo/timing-matrix): piloto, búsqueda y snapshots de fuentes.
- [timing-evidence/20261018](../../../archivo/timing-evidence/20261018): tablas y objetos versionados de la etapa inicial.
- [timing-audit](../../../archivo/timing-audit): diagnósticos, factibilidad, planes, recursos, limpieza y compresión.
- [timing-preparation](../../../archivo/timing-preparation): campañas preparadas/ejecutadas, cada una con su código, plan y resultados.
- [Censo diagnóstico](../../../archivo/timing-preparation/diagnostic_census_20261021/INFORME_ACTUAL.txt): endpoints y rutas locales.
- [Noche física](../../../archivo/timing-preparation/focused_physical_20261021/night_run_20261021/summary.json): selección final SATP009 y reglas de comparación.
- [91 MHz](../../../archivo/timing-preparation/pl0_91mhz_20261022): secuencia completa, reportes normales y AggressiveExplore.
- [Retiming 100 MHz](../../../archivo/timing-preparation/exp100_retiming_20261022): intentos, interrupciones y estimación de síntesis.

## Investigación e informe para presentar

[Timing CVA6 KR260 en PDF](../../../documentos/Timing_CVA6_KR260.pdf) es el informe existente del 25/10, de ocho páginas. Se conserva sin edición. Sus conclusiones absolutas sobre imposibilidad y algunas propuestas deben leerse con las [aclaraciones actuales](aclaraciones_documentales.md).

[Análisis local 100 MHz](../analisis_100mhz_kr260.md) reúne familias críticas y propuestas. Los cambios del CPU que menciona no están autorizados. [Síntesis de investigación del 27/10](../../../documentos/reports/Frecuencia%20del%20CVA6%20en%20FPGA.md) resume referencias externas.

| Notas originales | Fecha documental |
|---|---|
| [Flujo oficial CVA6](../../../documentos/research_notes/Frecuencia%20del%20CVA6%20en%20FPGA/oficial_cva6_fpga.md) | 27/10 |
| [Ports y publicaciones](../../../documentos/research_notes/Frecuencia%20del%20CVA6%20en%20FPGA/ports_y_papers.md) | 27/10 |
| [K26 y comparación](../../../documentos/research_notes/Frecuencia%20del%20CVA6%20en%20FPGA/k26_y_comparativa.md) | 27/10 |
| [Caminos críticos y técnicas](../../../documentos/research_notes/Frecuencia%20del%20CVA6%20en%20FPGA/caminos_criticos_y_tecnicas.md) | 27/10 |
| [CVA6 en Kria y Zynq UltraScale+](../../../documentos/research_notes/CVA6%20en%20Kria%20y%20Zynq%20UltraScale%2B/cva6_ports_zynq_kria.md) | 28/10 |
| [Otros núcleos en Kria](../../../documentos/research_notes/CVA6%20en%20Kria%20y%20Zynq%20UltraScale%2B/otros_nucleos_kria.md) | 28/10 |

## Índices completos y archivo

`inventario_archivos.jsonl.gz` contiene una fila por archivo dentro de los ámbitos listados en `alcance_archivo.json`: ruta relativa al workspace, tamaño, fecha y si se archivó su contenido. No enumera toda la computadora ni el Vivado instalado. Los árboles fuente congelados se inventarían, pero no se duplican como documentación.

`fuentes_documentales.json` identifica por SHA256 los contenidos seleccionados. `archivo_documental_20261029.tar.gz` almacena un objeto por hash y un índice de rutas; evita repetir contenido idéntico. Incluye el PDF, guías, notas, planes, scripts, configuraciones y evidencia compacta según los límites de tamaño declarados. Los reportes/censos grandes y binarios se conservan en su origen y se referencian; un registro de tamaño/fecha sin SHA no comprueba su contenido.

`auditorias/` conserva revisiones factuales de evidencia reciente, historia y operación. `validacion.json` registra la comprobación de enlaces, hashes de la copia, integridad del paquete de 91 MHz cuando esté disponible y preservación de los archivos modificados preexistentes. El registro de Git no representa un commit nuevo ni un push.

## Campaña CAST del 4 de noviembre

- [Registro nuevo y comparación por etapa](actualizacion_20261104_cast.md).
- [Evidencia y hashes de las métricas](auditorias/timings_20261104.json).
- [Fuentes y artefactos de las campañas](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/README.md).
- [Prueba de 120 MHz y controles de baja carga](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/README-120MHz.md).
- [Hashes de la actualización](SHA256SUMS_20261104.txt) y [archivo documental del corte](archivo_documental_20261104_cast.tar.gz).

## Paquete de 100 MHz del 5 de noviembre

- [Paquete, prueba en placa y resultados finales](actualizacion_20261105_paquete_100mhz.md).
- [Por qué dos implementaciones de CAST3 dieron distinto](comparacion_implementaciones_100mhz_20261104.md).
- [Evidencia y hashes de las métricas](auditorias/timings_20261105.json).
- [Paquete generado](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/paquete_100mhz_desde_cast3/LEEME.md) e [implementación con el reloj real](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/README-100MHz-real.md).
- [Hashes de la actualización](SHA256SUMS_20261105.txt) y [archivo documental del corte](archivo_documental_20261105_100mhz.tar.gz).

## Prueba en placa del 6 de noviembre

- [Registro de la prueba: resultados, FSBL y problemas encontrados](actualizacion_20261106_prueba_placa_ddr.md).
- [Evidencia: lecturas, capturas del ILA y logs](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/implementacion_ddr/prueba_placa_20261106/RESULTADO.md).
- [Guía paso a paso desde `xsdb`](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/implementacion_ddr/paquete_ddr_100mhz/LEEME.md).

Las rutas nuevas de CSV son absolutas cuando la campaña está fuera del workspace FPGA histórico. Se conservan las rutas relativas de las filas anteriores. Los manifiestos del 29 de octubre no se presentan como inventarios de estas campañas nuevas.
