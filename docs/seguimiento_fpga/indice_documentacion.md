# Índice central de la documentación del CVA6 en KR260

Organización del 4 de noviembre de 2026. La documentación de consulta está reunida
en esta carpeta: estado, comparaciones, tablas, PDF, guías técnicas, manual de
placa e investigación. Los originales se conservan en sus ubicaciones y no se
borró ningún archivo.

## Para continuar el trabajo

| Consulta | Abrir |
|---|---|
| Estado vigente del proyecto | [Registro principal](README.md) |
| Paquete de 100 MHz, prueba en placa y resultado final de 120 MHz | [Registro del 5 de noviembre](actualizacion_20261105_paquete_100mhz.md) |
| Dos y tres registros a 100 MHz e inicio de 120 MHz | [Comparación del 4 de noviembre](actualizacion_20261104_cast.md) |
| Por qué dos implementaciones de CAST3 a 100 MHz dieron distinto | [Comparación de implementaciones](comparacion_implementaciones_100mhz_20261104.md) |
| Resultados por etapa | [Resultados principales](resultados_clave.csv) |
| Implementaciones evaluadas a 100 MHz | [Evaluaciones](evaluaciones_100mhz.csv) |
| Decisiones y alcance | [Registro de decisiones](decisiones.csv) |
| Fuentes, identidad y recuperación | [Mapa documental](mapa_documental.md) |

Las copias de la biblioteca tienen fecha propia. Para incorporar un resultado
nuevo se actualiza el registro principal y sus tablas; los informes históricos
conservan su alcance. Los tres PDF son anteriores a la campaña CAST del 4 de
noviembre y deben leerse junto a la comparación actual.

## PDF para consultar

- [Timing_CVA6_KR260.pdf](biblioteca_20261104/pdf/2026-10-25_Timing_CVA6_KR260.pdf)
- [CVA6_KR260_estado_reunion_20261030.pdf](biblioteca_20261104/pdf/2026-10-30_Estado_reunion.pdf)
- [Manual_CVA6_KR260_90_9MHz.pdf](biblioteca_20261104/pdf/2026-10-30_Manual_placa_90_9MHz.pdf)

## Arquitectura e integración

- [kr260_bootrom_memory_test.md](biblioteca_20261104/arquitectura/kr260_bootrom_memory_test.md)
- [kr260_ddr_integration.md](biblioteca_20261104/arquitectura/kr260_ddr_integration.md)
- [kr260_ila_vio.md](biblioteca_20261104/arquitectura/kr260_ila_vio.md)
- [kr260_lint.md](biblioteca_20261104/arquitectura/kr260_lint.md)
- [kr260_memory_path.md](biblioteca_20261104/arquitectura/kr260_memory_path.md)
- [kr260_port_analysis.md](biblioteca_20261104/arquitectura/kr260_port_analysis.md)
- [kr260_ps_ddr_architecture.md](biblioteca_20261104/arquitectura/kr260_ps_ddr_architecture.md)
- [kr260_versionado_y_recuperacion.md](biblioteca_20261104/arquitectura/kr260_versionado_y_recuperacion.md)

## Campañas y automatización de timing

- [timing_evidence.md](biblioteca_20261104/campanas/timing_evidence.md)
- [timing_matrix.md](biblioteca_20261104/campanas/timing_matrix.md)
- [timing_sweep.md](biblioteca_20261104/campanas/timing_sweep.md)
- [README.md](biblioteca_20261104/campanas/guia_CAST_100MHz.md)
- [README-120MHz.md](biblioteca_20261104/campanas/guia_CAST3_120MHz_baja_carga.md)

## Prueba en placa y manual editable

- [PARA_PLACA_CON_GONZA_20261030.md](biblioteca_20261104/placa/PARA_PLACA_CON_GONZA_20261030.md)
- [README.md](biblioteca_20261104/placa/guia_automatizacion.md)
- [MANUAL_PLACA.txt](biblioteca_20261104/placa/MANUAL_PLACA.txt)
- [RUTAS_IMPORTANTES.txt](biblioteca_20261104/placa/RUTAS_IMPORTANTES.txt)
- [generar_manual.py](biblioteca_20261104/placa/generar_manual.py)
- [VERIFICACION.json](biblioteca_20261104/placa/VERIFICACION.json)

## Reunión del 30 de octubre

- [README_ENTREGA.md](biblioteca_20261104/reunion_20261030/README_ENTREGA.md)
- [RESUMEN_REUNION.md](reunion_20261030/RESUMEN_REUNION.md)

## Investigación y análisis

- [analisis_100mhz_kr260.md](biblioteca_20261104/investigacion/analisis_100mhz_kr260.md)
- [cva6_ports_zynq_kria.md](biblioteca_20261104/investigacion/kria_zynq/cva6_ports_zynq_kria.md)
- [otros_nucleos_kria.md](biblioteca_20261104/investigacion/kria_zynq/otros_nucleos_kria.md)
- [caminos_criticos_y_tecnicas.md](biblioteca_20261104/investigacion/frecuencia_fpga/caminos_criticos_y_tecnicas.md)
- [k26_y_comparativa.md](biblioteca_20261104/investigacion/frecuencia_fpga/k26_y_comparativa.md)
- [oficial_cva6_fpga.md](biblioteca_20261104/investigacion/frecuencia_fpga/oficial_cva6_fpga.md)
- [ports_y_papers.md](biblioteca_20261104/investigacion/frecuencia_fpga/ports_y_papers.md)
- [Frecuencia del CVA6 en FPGA.md](biblioteca_20261104/investigacion/resumen_investigacion_20261027.md)

## Organización y respaldo

- [DOCUMENTACION_CVA6.md](biblioteca_20261104/organizacion/DOCUMENTACION_CVA6.md)
- [CVA6_VIVADO_WORKSPACE.md](biblioteca_20261104/organizacion/CVA6_VIVADO_WORKSPACE.md)
- [RESPALDO_EXTERNO_20261029.md](biblioteca_20261104/organizacion/RESPALDO_EXTERNO_20261029.md)

## Conservación y enlaces

Las copias PDF, TXT, JSON y el generador del manual son idénticas a sus fuentes.
En las copias Markdown se ajustaron enlaces existentes para que conduzcan a
otra copia de esta biblioteca o al archivo original conservado. El contenido
de los originales no se modificó. Cuando ya había una copia idéntica dentro de
la carpeta central, se reutilizó esa copia.

Los reportes de Vivado, fuentes RTL, checkpoints, bitstreams y configuraciones de
las campañas mantienen sus rutas. Están referenciados desde el registro, sin
mover los archivos que utiliza la prueba activa.

[Manifiesto de originales, copias y enlaces](biblioteca_20261104/manifest.json)
y [hashes de esta organización](biblioteca_20261104/SHA256SUMS.txt).

Los índices y archivos documentales anteriores conservan sus fechas y hashes.
No se modificaron ni reemplazaron los cortes del 29 de octubre y de la campaña
CAST del 4 de noviembre. El corte del 5 de noviembre tiene hashes y archivo propios:
[hashes](SHA256SUMS_20261105.txt) y
[archivo documental](archivo_documental_20261105_100mhz.tar.gz).
