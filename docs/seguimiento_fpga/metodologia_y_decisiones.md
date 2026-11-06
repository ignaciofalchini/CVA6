# Metodología y decisiones de las pruebas

## Objetivo y límites

En el corte histórico hasta el 29 de octubre se priorizaba 100 MHz mediante opciones de Vivado, conservando RTL, parámetros y microarquitectura. Las menciones conversacionales a GHz o a 1000 Hz no redefinen esos objetivos.

El 4 de noviembre se autorizó la campaña específica de registros de CAST: dos registros con reparto 0/1/1 y tres con reparto 1/1/1 (`LAT_CONV=3`, un ciclo adicional de conversión). También se autorizó probar CAST3 a 120 MHz con baja carga. Esta ampliación concreta no autoriza otros cambios en ISA, PMP, TLB, cachés o pipeline. Ver [alcance y comparación](actualizacion_20261104_cast.md).

Esa misma noche se autorizó una implementación con el reloj del PS a 100 MHz y, como no cerró, generar el paquete desde el checkpoint de CAST3 que sí cerró. El checkpoint no se modificó y el XSA combina su bitstream con los archivos del PS en IOPLL/10. Ver [paquete y alcance](actualizacion_20261105_paquete_100mhz.md).

La replicación dirigida de drivers en la netlist y el retiming como opción de herramienta deben registrarse como transformaciones de Vivado. Su aceptación exige evidencia de preservación funcional compatible con el ensayo; el cambio autorizado de CAST se registra por separado con su latencia y sus comprobaciones. Un candidato rechazado por integridad no puede convertirse en ganador sólo por sus slacks.

## Qué se mide

| Dato | Interpretación |
|---|---|
| WNS | Peor margen de setup; un valor negativo impide el cierre |
| TNS y endpoints negativos | Extensión de las violaciones; complementan al WNS |
| WHS / THS | Hold: revisar mínimos y cantidad de violaciones |
| WPWS / TPWS | Ancho de pulso y sus violaciones |
| Bus skew | Restricciones de dispersión entre señales cuando existan |
| check_timing y relojes | Cobertura real del análisis y consistencia de restricciones |
| Ruteo, DRC y metodología | Integridad física y avisos pendientes |
| Duración, RAM, swap, CPU y disco | Viabilidad de la ejecución, sin confundir métricas de Vivado y del sistema |

Que una síntesis termine no implica cierre de timing. Sus retardos de interconexión son estimados; pueden empeorar o mejorar después del placement y routeo. La aceptación de cierre necesita el reporte final ruteado, sin violaciones de setup, hold ni pulso, restricciones y bus skew revisados, ruteo completo y evaluación de DRC/metodología. La validación funcional en placa es un hito separado.

## Comparaciones justas

- Registrar la receta ejecutada y el punto de partida exacto, con hashes y manifiesto, no sólo el nombre de una estrategia.
- Separar barrido de síntesis con implementación controlada, barrido de implementación sobre una síntesis fija y optimización local sobre DCP ruteado.
- Reutilizar resultados sólo si coinciden fuentes, restricciones, netlist y parámetros relevantes. Una política homónima sobre otra síntesis es otro experimento.
- No sumar ventanas solapadas ni el tiempo del top a una espera que ya lo incluye. Elapsed de etapa y tiempo de calendario pueden diferir por pausas, reconstrucción de reportes o errores de automatización.
- Para medias y distribuciones, usar una población fija de endpoints e identificarla por hash. No comparar como si fueran la misma población los 96.433 endpoints de la tanda 100 MHz y los 96.451 del nuevo build de 90,9 MHz.
- Guardar baseline, resultado final y candidatos no adoptados. Un mejor TNS con WNS negativo sigue sin cerrar.

## Clasificación de intentos

| Estado documental | Qué cuenta |
|---|---|
| Planeado | Receta definida; no demuestra que se haya ejecutado |
| Interrumpido antes de optimización | No aporta una evaluación de esa política física |
| Error de automatización | Falló el script o la API; no prueba que la estrategia física sea mala |
| Completado válido sin mejora | Comparación física utilizable, conserva referencia |
| Completado válido con mejora | Mejora medida; indicar si fue adoptado |
| Rechazado por integridad | Excluir de ganadores y estadísticas de resultados válidos |
| Cierre STA | Cumple el análisis final con su alcance y exclusiones documentados |
| Validado en placa | Prueba funcional identificada, frecuencia y artefactos coherentes |

## Por qué el WNS no acompañó al TNS en la campaña histórica a 100 MHz

El análisis del mejor resultado histórico identifica grupos independientes de CAST, PMP y FMA cerca de −0,53 a −0,55 ns, además de caché, MMU y operandos. Mejorar sólo SATP o un subconjunto FMA reduce violaciones sin corregir necesariamente el peor camino de CAST/PMP. En los caminos críticos examinados, el ruteo representa una parte importante del retardo; las intervenciones locales pueden redistribuir el problema hacia otra conexión.

El censo histórico cubrió los 1716 endpoints negativos de su checkpoint, un peor camino por endpoint; no todos los caminos combinatorios posibles del CPU. Ver [censo y conclusiones](../../../archivo/timing-preparation/diagnostic_census_20261021/INFORME_ACTUAL.txt). Los nombres/bit de SATP cambiaron entre netlists: las réplicas antiguas de un bit no equivalen a optimizar el origen crítico de una netlist nueva.

## Los 75 endpoints del JTAG

Los reportes finales enumeran 75 pines excluidos por clock constante, todos dentro de `i_ariane_kr260/i_dmi_jtag/i_dmi_cdc/`. El conjunto coincide con el gold SATP009 y no representa 75 violaciones de setup. El DMI-JTAG propio del CVA6 está inactivo; el reloj BSCAN/`INTERNAL_TCK` del debug hub es distinto y aparece analizado a 20 MHz. No se agregaron excepciones para ocultar fallos.

Ver [check_timing final](../../../archivo/timing-preparation/pl0_91mhz_20261022/reports_aggressive/check_timing.rpt) y [auditoría reciente](auditorias/reciente.json). Si se habilitara ese JTAG, cambia el alcance y debe revisarse su restricción; el diagnóstico actual corresponde a la integración documentada.

## Investigación externa

Las notas del 27 y 28 de octubre conservan enlaces a repositorios, issues, documentación AMD y publicaciones. Distinguir frecuencia objetivo declarada, estimación post-síntesis, reporte ruteado y funcionamiento en placa. No comparar directamente RV32 sin FPU o dispositivos de otra velocidad/voltaje con este RV64 con FPU en K26 -2LV. La consolidación preserva esa investigación fechada; no constituye una nueva comprobación de todos sus enlaces o conclusiones.

## Comparación y cuantización en la campaña CAST

CAST2 y CAST3 modifican el reparto de registros de conversión y tienen poblaciones distintas de endpoints. Comparar cierre, márgenes y latencia explícitos; no deducir una mejora proporcional de rendimiento ni una media sobre una población fija a partir de sus TNS globales. Los reportes de síntesis reconstruidos son estimaciones de corridas ya terminadas, no ejecuciones nuevas ni cierre físico.

Para el objetivo de 120 MHz, Vivado cuantiza 8,333333333 ns a 8,333 ns y 4,1666666665 ns a 4,167 ns. El manifiesto conserva el objetivo y el reporte el período observado. La tolerancia de lectura se limita a ese redondeo de 1 ps. WNS o WHS reportados como 0,000 ns se interpretan junto con el estado MET y cero endpoints negativos; no equivalen a margen holgado.
