# Aclaraciones de la documentación histórica

Estos puntos evitan interpretar un documento antiguo como estado actual. Se conservan los originales, sus fechas y su contenido.

| Afirmación o registro anterior | Lectura vigente y fuente |
|---|---|
| `CURRENT_STATUS.txt` del 22/10 anuncia un waiter activo | Es anterior al reinicio del 22/10. La consulta del 29/10 no encontró unidades CVA6 activas. Ver auditoría operativa |
| “Retiming no probado en KR260” en un encabezado del análisis | El mismo archivo agrega debajo el ensayo del 22/10: síntesis terminada y cero movimientos. El encabezado quedó desactualizado |
| “No se ejecutó implementación” del ensayo de retiming | Vale para el último intento; uno anterior sí inició implementación y fue interrumpido. No produjo un resultado final adoptado |
| Cero retiming se debe sólo a que la FPU pasa en síntesis | El log registra también FF bloqueados por múltiples relojes. No se aisló una causa única |
| “Todo agotado” o “100 MHz imposible” | Los ensayos no cerraron a 100 MHz. Eso no es una prueba universal de imposibilidad, ni de haber evaluado todo el espacio de directivas, clocks y colocación |
| “Para superar 90,9 MHz hay que modificar el CPU” | Es una generalización; esos mismos informes enumeran MMCM/raíz de reloj y otras hipótesis no medidas. No hay garantía de mejora ni autorización para cambiar el CPU |
| Fmax 94,8 MHz | Estimación desde el checkpoint ruteado a 100 MHz con WNS −0,553 ns; no cierre ni prueba en placa a esa frecuencia |
| Fmax 88,18 MHz en `routed_initial_estimate.json` | Estimación de una etapa intermedia anterior al post-route final de 90,9 MHz |
| Inventario actual de los 75 pines pendiente en JSON de las 12:41 | Los reportes finales posteriores sí enumeran el conjunto, idéntico al gold009; todos pertenecen al DMI-JTAG inactivo |
| “JTAG deshabilitado” equivale a todo el debug apagado | El DMI-JTAG del CPU está inactivo; BSCAN/ILA/VIO es otra infraestructura y su reloj TCK sí se analiza |
| Un bitstream de `impl_1` representa el cierre 91 MHz | `impl_1` quedó en −0,065 ns. El paquete cerrado usa el DCP posterior AggressiveExplore y su propio BIT/LTX/XSA |
| El archivo continuo cubre todas las pruebas | El colector de `timing-evidence/20261018` estaba configurado para piloto y búsqueda inicial; no toda la etapa física posterior |
| Un resultado aceptado es el ganador | En FMA010 el análisis fue válido y no se adoptó por una ligera regresión en la media global fija |
| La noche terminó al agotar nueve horas | Terminó antes por agotar la cola/cupos de composiciones de esa versión. No demuestra que todas las composiciones posibles fueran probadas |
| Documentación antigua de BRAM o DDR baja describe el sistema actual | Son variantes anteriores. La integración posterior usa la ventana alta DDR del PS y el paquete cerrado identifica su configuración |
| Frecuencia nominal del XDC equivale a frecuencia programada del PS | Las primeras copias pedían 150 MHz y el PS calculaba 142,855713 MHz, aunque STA usara 10 ns. El paquete cerrado91 corrige PL0 a IOPLL/11 |
| Hay o no hay CVA6 con FPU en Kria según notas del mismo día | Distinguir configuración pública objetivo, reporte STA y ejecución demostrada: una nota enumera KR260/FPU a 60 MHz como target sin WNS. No prueba cierre ni funcionamiento |

Las fuentes precisas por hallazgo se guardan en [auditoría reciente](auditorias/reciente.json), [auditoría histórica](auditorias/historico.json) y [auditoría operativa](auditorias/operacion.json). Las propuestas históricas de PMP precalculado, reducción de TLB/caché y otros cambios permanecen fuera del alcance vigente. El reparto de registros de CAST y `LAT_CONV=3` tienen autorización específica en la campaña del 4 de noviembre; no se extiende a otras unidades o parámetros.

La investigación exhaustiva de frecuencia dejó un recolector y estimaciones iniciales. No se generó una colección final completa ni un watcher operativo; no contarlos como trabajo ya ejecutado. La consolidación del 29 de octubre incorporó los reportes finales disponibles en ese corte. La campaña CAST del 4 de noviembre es una ejecución posterior identificada por separado.

## Aclaraciones del 4 de noviembre

| Lectura que necesita contexto | Estado confirmado |
|---|---|
| No hay cierre a 100 MHz | Era el estado del corte de octubre. CAST3 cerró STA a 100 MHz el 4 de noviembre; hardware pendiente. |
| Un reporte de síntesis negativo contradice el cierre final | La síntesis usa conexiones estimadas. CAST3 pasó de WNS −0,421 ns estimado a 0,000 ns final, con cero endpoints negativos. |
| WNS 0,000 ns deja margen para 120 o 150 MHz | Los márgenes redondean a cero. La implementación a 120 MHz está pendiente y no se ejecutó una prueba nueva a 150 MHz en esta campaña. |
| La prueba de 120 MHz ya falló definitivamente | WNS −2,088 ns corresponde a síntesis. Falta el veredicto final ruteado. |
| El CPU de tres registros es idéntico ciclo a ciclo al de dos | CAST3 agrega un ciclo de conversión. La comparación de rendimiento debe contemplarlo. |
| El reloj físico quedó configurado a 100 o 120 MHz | Son objetivos de STA en estas copias; la configuración física del PS y la validación en placa quedan pendientes. |

Ver [entrada completa con reportes y alcance](actualizacion_20261104_cast.md). Los inventarios, archivos comprimidos y hashes del 29 de octubre conservan ese corte; los cambios del 4 de noviembre tienen evidencia y manifiesto nuevos.

## Aclaraciones del 5 de noviembre

Reemplazan las filas anteriores sobre 120 MHz y sobre el reloj físico.

| Lectura que necesita contexto | Estado confirmado |
|---|---|
| La implementación de 120 MHz está pendiente | Terminó sin cierre: WNS −1,806 ns y 18.654 endpoints de setup negativos. |
| Cerrar 100 MHz exige cambiar la FPU y la PMP | Lo afirma el informe de investigación del 27 de octubre. CAST3 cerró cambiando CAST, sin tocar PMP. |
| Como una implementación nueva no cerró, 100 MHz no vale | El cierre de CAST3 sigue siendo válido a 10 ns. La implementación nueva quedó cerca del 2 % abajo, y el margen de CAST3 era 0,000 ns. |
| Cualquier implementación nueva de este RTL cierra a 100 MHz | No. Una ya no cerró, sin margen para absorber esa variación. |
| El bitstream de 100 MHz salió de la implementación con el PS a 100 MHz | Salió del checkpoint de CAST3 que cerró. El reloj de 100 MHz lo programa el FSBL. |
| Vivado generó el XSA de 100 MHz directamente | Es una combinación: bitstream del checkpoint cerrado y archivos del PS en IOPLL/10. Regenerarlo desde ese checkpoint volvería a IOPLL/11. |
| El paquete de 100 MHz ya funciona en placa | Compiló y sus hashes se comprobaron, pero no se ejecutó en hardware. |
| Un PASS de `cva6 ensayo` valida la FPU o la frecuencia | Esa prueba cubre BootROM y DDR. No ejercita la FPU ni mide la frecuencia alcanzada. |
| `fpnew_cast_multi.sv` solo cambia el reparto de registros | También corrige la extensión de signo de `fcvt.w` y `fcvt.wu` en RV64, lo que cambia resultados, y agrega una salida sin uso. |
| La guía de placa del 30 de octubre y el manual cubren 100 MHz | Describen 25 y 90,9 MHz y conservan su fecha. Para 100 MHz, usar la [entrada del 5 de noviembre](actualizacion_20261105_paquete_100mhz.md). |

## Aclaraciones del 6 de noviembre

| Lectura que necesita contexto | Estado confirmado |
|---|---|
| El repositorio conserva `LAT_CONV=2`, el BD a 90,9 MHz y `fp_cvt.opLat = 2` | Era el estado de los registros anteriores. Los commits `9c333f3fe` y `793c70103` pasan a `LAT_CONV=3`, IOPLL/10 y `opLat = 3`. |
| Implementar desde el repositorio reproduce el cierre a 100 MHz | No está garantizado: otra implementación del mismo RTL dio WNS −0,208 ns. La referencia sigue siendo el DCP cerrado, que no está en git. |
| Los cambios ya están en GitHub | Los commits son locales: la rama no está en ningún remoto. |
