# Por qué dos implementaciones de CAST3 a 100 MHz dieron distinto

Corte: **4 de noviembre de 2026, 23:13, hora de Córdoba**. Plataforma KR260,
K26 `xck26-sfvc784-2LV-c`, Vivado 2026.1, top `kr260_top`.

**La diferencia final fue de 0,208 ns, cerca del 2 % de frecuencia.** Una corrida
terminó con WNS 0,000 ns y la otra con −0,208 ns, equivalente a unos 98 MHz. Los
resultados son parecidos, pero el cierre es un umbral y la primera corrida ya
estaba sin margen. El cierre de CAST3 sigue siendo válido a 10 ns.

- **Corrida que cerró:** `recuperacion_20261104/cast3`, 14:50.
- **Corrida nueva:** `implementacion_100MHz_reloj_real/cast3`, 20:52.

## Resultado por etapa

| Etapa | Cerró: WNS / TNS (ns) | Nueva: WNS / TNS (ns) | Diferencia de WNS |
|---|---|---:|---:|
| Síntesis | −0,421 / −36,999 | −0,415 / −35,386 | 0,006 a favor de la nueva |
| Después de colocar, al iniciar `phys_opt` | −0,302 / −65,538 | −0,987 / −1.061,998 | 0,685 |
| `phys_opt`, antes de rutear | +0,007 / 0,000 | −0,417 / −208,362 | 0,424 |
| Después de rutear | −0,101 / −14,427 | −0,580 / −510,834 | 0,479 |
| Final | **0,000 / 0,000** | **−0,208 / −90,293** | **0,208** |

La síntesis dio igual y la diferencia aparece al colocar. Las etapas siguientes
la reducen de 0,685 a 0,208 ns, pero no alcanzan a cruzar el cero. Al final fallan
1.014 de 96.693 endpoints de setup en la corrida nueva, con un promedio de unos
0,089 ns por endpoint. Hold cumple en ambas y el ruteo terminó sin errores.

## Qué fue igual y qué cambió

| Elemento | Corrida que cerró | Corrida nueva |
|---|---|---|
| RTL de CVA6 y FPU (`LAT_CONV=3`, 1/1/1) | Igual | Igual, por hash |
| Estrategias y directivas | Iguales | Iguales |
| Hilos (síntesis / implementación) | 2 / 4 | 2 / 4 |
| Checksum de la síntesis | `2d5da2aa` | `2d5da2aa` |
| Peor camino de síntesis | 10,154 ns, 36 niveles | 10,154 ns, 36 niveles |
| Divisor de PL0 en el BD | IOPLL/11 | IOPLL/10 |
| Reloj de 10 ns | `create_clock` tardío sobre el PS a 11 ns | XDC del PS a 10 ns |
| Discrete jitter / incertidumbre | 0,324 / 0,166 ns | 0,312 / 0,160 ns |
| Último paso después de rutear | `Explore` | `Explore` y `AggressiveExplore` |

Los archivos generados del PS difieren en metadatos de frecuencia y jitter, sin
cambios de lógica en la síntesis. Las opciones de corrida solo difieren en la
lista de reportes. Los 0,006 ns de diferencia en síntesis coinciden con la
diferencia de incertidumbre del reloj.

## Cómo se propagó

1. El cambio a IOPLL/10 modificó los atributos del PS y bajó 6 ps la incertidumbre
   del reloj.
2. La síntesis no cambió, pero el checksum del diseño enlazado ya es distinto al
   empezar `opt_design`: `24ba854c6` contra `23b98739f`.
3. Retarget, Constant Propagation, Sweep y BUFG hicieron exactamente lo mismo.
   **Remap es la primera etapa con otros cambios lógicos:** creó y quitó 8.775 y
   7.828 celdas en una corrida, contra 8.235 y 7.240 en la otra.
4. `place_design` partió de otro netlist. Por ejemplo, LUT Combining quitó 1.440
   celdas contra 897.
5. La colocación resultante fue peor: WNS −0,987 ns contra −0,302 ns. Las
   optimizaciones siguientes trabajaron sobre esa colocación.
6. Cambiaron los caminos que limitan. Entre los 100 peores, las fuentes principales
   eran `pmpaddr_q` (56) y la FPU (29) en la corrida que cerró, e
   `i_issue_read_operands` (62) y la FPU (38) en la nueva.

## Qué se descartó

- **Síntesis:** el checksum y el peor camino coinciden.
- **Más jitter en el reloj real:** la incertidumbre bajó 6 ps con IOPLL/10.
- **Congestión:** el uso de ruteo no empeoró, con 22,05 % vertical y 22,50 %
  horizontal, contra 23,65 % y 22,98 %.
- **Hilos o directivas distintos:** coinciden en todas las etapas comunes.
- **Un error de ruteo:** las 88.388 redes quedaron ruteadas, sin errores.

## Por qué no contradice que las implementaciones den parecido

Los resultados sí fueron parecidos: 100 MHz contra unos 98 MHz. La iteración
también se ve en los datos, porque la diferencia bajó de 0,685 a 0,208 ns. Lo que
la iteración no garantiza es llegar al mismo punto: cada corrida mejora desde su
propia colocación, y una herramienta heurística puede terminar en resultados algo
distintos.

La sensibilidad es alta porque hay muchos caminos casi críticos. Los 100 peores
caben en 0,036 ns en la corrida que cerró, y en 0,039 ns en la nueva. Con margen
0,000 ns, un corrimiento de ese tamaño ya deja muchos endpoints en negativo.

Esta variación tampoco es rara en la bibliografía. AMD menciona diseños que no
cumplen timing de forma consistente y recomienda comparar una corrida que cierra
con una que no. Intel describe cómo un cambio en la colocación inicial altera las
optimizaciones siguientes. Efinix informa de 10 a 20 % de variación de fMAX en un
barrido de 10 semillas, y un trabajo reciente con un RISC-V en FPGA observa unos
38 MHz de variación en 30 semillas de ruteo. Esas cifras no son de este diseño ni,
salvo AMD, de Vivado: solo muestran que este fenómeno es conocido.

## Qué no está demostrado

- **La causa interna exacta.** Los datos ubican el punto de divergencia, pero
  Vivado no muestra por qué Remap decidió distinto. No se puede separar si pesaron
  los 6 ps, los atributos del PS o el orden de las restricciones.
- **La repetibilidad.** No se repitió ninguna corrida con entradas idénticas, y no
  se encontró una declaración de AMD sobre resultados idénticos con igual entrada.
- **El alcance de la variación.** Con una sola corrida nueva no se puede estimar qué
  tan seguido este diseño cierra a 100 MHz.

## Consecuencia práctica

El `final.dcp` que cerró sigue siendo válido a 10 ns. Su análisis usó 0,166 ns de
incertidumbre, 6 ps más que los 0,160 ns calculados con IOPLL/10, y el netlist de
síntesis es el mismo. La frecuencia real la programa el FSBL, de modo que el
bitstream puede salir de ese checkpoint sin reimplementar.

Si se cambia el RTL o se implementa de nuevo, no se debe asumir que 100 MHz vuelva
a cerrar. El margen actual es 0,000 ns, sin reserva para esa variación.

En la misma jornada, CAST3 a 120 MHz terminó sin cierre, con WNS −1,806 ns y
18.654 endpoints fallando.

## Paquete generado desde el checkpoint que cerró

A las 23:17 se generaron el bitstream, los probes y el XSA desde ese `final.dcp`, sin
reimplementar, en `Automatizacion-FPU-100MHz/paquete_100mhz_desde_cast3/`. El XSA usa
el bitstream del DCP cerrado y los archivos del PS con IOPLL/10, que solo difieren
en la frecuencia de PL0 y la fecha del `hwh`.

Al reabrir el DCP, el análisis repitió 0,000 ns de setup y hold a 10 ns, y el DRC del
bitstream terminó sin errores. HSI abrió el XSA y el FSBL con el parche de reset
compiló sin errores: `kr260_fsbl_100mhz_patched.elf`. Frente al FSBL de 91 MHz, en
su binario cargado cambian dos instrucciones, ambas por el divisor de PL0, y la fecha
y hora de compilación. `cva6 ensayo --frecuencia 100` ya usa este paquete. Falta
probar en placa.

## Evidencia

En `~/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/`:

- `recuperacion_20261104/cast3/reports/`: `run.console.log`, `finalize.console.log`,
  `routed_before_final/timing_summary.rpt`, `critical_setup.rpt`, `run_settings.txt`.
- `implementacion_100MHz_reloj_real/cast3/reports/`: `run.console.log`,
  `result.json`, `critical_setup.rpt`, `run_settings.txt`.
- `implementacion_100MHz_reloj_real/manifest.json`: hashes y archivos que cambió
  IOPLL/10.

Los reportes de caminos solo listan los 100 peores de cada corrida, y no son los
mismos caminos, por lo que esa comparación es indicativa.

## Fuentes externas

- [AMD UG906, Floorplanning](https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/Floorplanning?contentId=n6PsHn3kiIUSJrMCoLOYoA)
- [AMD UG906, Information Reuse](https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/Information-Reuse)
- [Intel, Change Fitter Placement Seeds](https://www.intel.com/content/www/us/en/docs/programmable/683145/21-3/change-fitter-placement-seeds.html)
- [Efinix, Seed Sweeping](https://www.efinixinc.com/docs-html/efinity/topics/tim-seed-sweep.html)
- [Pipeline Stage Resolved Timing Characterization of FPGA and ASIC Implementations of a RISC V Processor](https://arxiv.org/pdf/2512.13866)
