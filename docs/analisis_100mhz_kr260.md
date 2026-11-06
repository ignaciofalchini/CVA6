# ¿Puede el CVA6 correr a 100 MHz en la KR260 sin modificar el CVA6?

Fecha: 2026-10-22. Configuración: `cv64a6_imafdc_sv39`, K26 `xck26-sfvc784-2LV-c`,
Vivado 2026.1, clock del PS (`pl_clk0`) como único reloj del CVA6.

## Respuesta corta

Con lo medido, **es poco probable**. Lo que está cerrado hoy es **90,908 MHz**
(paquete `corev_apu/fpga/software/kr260_ps_boot/timing_closed_91mhz_2026-10-22/`).
El mejor resultado a 100 MHz, después de días de optimización física, quedó en
WNS −0,553 ns: un techo efectivo de unos 94–95 MHz.

El experimento con retiming en síntesis (como el flujo FPGA oficial de CVA6) ya
se hizo el mismo día y **no movió ningún registro**: ver "Resultado del
experimento con retiming" más abajo. El grupo PMP, que por sí solo ya impide los
100 MHz, no tiene ninguna palanca medida que lo resuelva sin tocar el CVA6.

## Qué habría que ganar

Peor slack por familia de caminos en el mejor checkpoint a 100 MHz
(`009_restruct_SATP`, 1285 endpoints fallando):

| Familia (origen) | Endpoints | Peor slack | Mediana |
|---|---:|---:|---:|
| FPU, conversión (CAST) | 301 | −0,553 ns | −0,358 ns |
| PMP (CSR `pmpaddr`/`pmpcfg`) | 521 | −0,541 ns | −0,262 ns |
| FPU, FMA y otros grupos | 181 | −0,529 ns | −0,307 ns |
| Caché | 70 | −0,429 ns | −0,256 ns |
| MMU/TLB | 107 | −0,266 ns | −0,133 ns |
| Operandos | 105 | −0,240 ns | −0,118 ns |

Composición del peor camino de las tres familias críticas:

| Familia | Niveles | Datapath | Lógica | Ruteo | Skew de clock | Incertidumbre |
|---|---:|---:|---:|---:|---:|---:|
| CAST | 35 | 10,747 ns | 4,326 ns | 6,421 ns (60 %) | +0,293 ns | 0,142 ns |
| PMP | 31 | 10,188 ns | 3,586 ns | 6,602 ns (65 %) | −0,255 ns | 0,142 ns |
| FMA | 28 | 10,358 ns | 3,656 ns | 6,702 ns (65 %) | −0,075 ns | 0,142 ns |

**Conclusión de esta tabla:** tres partes independientes del core (CAST, PMP y
FMA) tienen que ganar 0,53–0,55 ns cada una, al mismo tiempo. Arreglar una sola
no mueve el WNS. Eso explica por qué las pruebas dirigidas a un grupo (CAST,
SATP, FMA) bajaron el TNS pero nunca el WNS.

## Lo que ya está agotado

| Prueba | Resultado a 100 MHz |
|---|---|
| Matriz de estrategias síntesis × implementación | −1,294 a −0,665 ns |
| Optimización física post-route (restruct, pines, réplicas, reruteo, ECO) | mejor −0,553 ns (~0,11 ns sobre la estrategia por defecto) |
| `phys_opt_design -clock_opt` post-route | sin cambio (−0,553 ns) |
| Reruteos de la red CAST | sin cambio o peor (−0,617 ns) |

A 90,9 MHz el flujo estándar dejó −0,065 ns y una pasada de
`phys_opt_design -directive AggressiveExplore` lo cerró con +0,001 ns.

## Palancas que no modifican el CVA6

### 1. Retiming en síntesis (no probado en la KR260)

- El flujo oficial lo activa: `corev_apu/fpga/scripts/run.tcl` hace
  `set_property STEPS.SYNTH_DESIGN.ARGS.RETIMING true [get_runs synth_1]`.
- La corrida del flujo oficial en la VC707 sintetizó con `-global_retiming on`
  y movió **524 registros dentro de `fpnew_top`** (208 hacia adelante,
  316 hacia atrás). En `pmp`, `cva6_tlb` y `cva6_mmu` movió **0**.
- El proyecto KR260 sintetiza sin retiming (`synth_design -top kr260_top -part …`),
  y la campaña lo dejó fuera a propósito ("sin retiming").
- No cambia el RTL ni la latencia en ciclos: mueve registros a través de lógica
  combinacional conservando el comportamiento en los límites del módulo.
- **Efecto esperado:** puede mejorar CAST y FMA (482 endpoints). No ayuda a PMP,
  caché ni MMU. La ganancia en la FPU no está medida en este dispositivo.

#### Resultado del experimento con retiming (2026-10-22)

Runs separados `synth_2`/`impl_2`, constraint set `constrs_exp100` (10 ns sólo
para análisis; el PS sigue a 90,9 MHz). Archivos en
`timing-preparation/exp100_retiming_20261022/`.

| Síntesis | Resultado del retiming |
|---|---|
| 4 procesos | sin resultado: se agotaron RAM y swap (OOM) |
| 2 procesos | resumen `-11`, 0 registros movidos en los 50 módulos |
| 1 proceso, no incremental | resumen `-11`, 0 registros movidos (`synth_design … -global_retiming on -incremental_mode off`) |

Causa: el retiming de síntesis decide con los retardos *estimados* por la
síntesis, que no incluyen el ruteo real. Timing estimado del checkpoint de
síntesis a 10 ns:

| Familia | Slack estimado en síntesis | Slack real post-route (campaña) |
|---|---:|---:|
| FPU (CAST) | +0,053 ns (39 niveles) | −0,553 ns |
| PMP | −0,145 ns (36 niveles) | −0,541 ns |
| Operandos | +0,301 ns | −0,240 ns |
| SATP | +2,651 ns | −0,504 ns |

Para la síntesis la FPU ya cumple, así que el retiming no tiene nada que mejorar.
El único camino negativo es PMP, que nace en registros CSR y no se puede
retemporizar. La diferencia con la VC707 es que ahí, a 50 MHz en un Virtex-7,
la síntesis sí veía la FPU fallando.

Variantes que quedan y por qué no cambian la conclusión:

- Sobre-restringir la síntesis (por ejemplo 8,5 ns) para forzar el retiming en
  la FPU: puede mejorar CAST/FMA, pero no PMP.
- Retiming físico en implementación (`phys_opt_design -retime`): usa retardos
  con ubicación real, pero tampoco puede mover los registros CSR de PMP.

### 2. Clock: MMCM y raíz del árbol de reloj (no probado)

- `pl_clk0` sale de un PLL del PS con jitter discreto de 0,276 ns, lo que da una
  incertidumbre de 0,142 ns.
- El peor camino PMP pierde además 0,255 ns por skew negativo.
- Generar el clock del CVA6 con un MMCM en `kr260_top` (el wrapper, no el CVA6)
  y ubicar la raíz del árbol cerca del core (`USER_CLOCK_ROOT`) podría bajar la
  incertidumbre y el skew. Es la única palanca no probada que actúa sobre PMP.
- **Efecto esperado:** desde decenas de ps hasta ~0,1–0,2 ns en PMP si mejora el
  skew. Es una estimación, no una medida.
- Costo: cambio en el wrapper y en el BD (el reloj de HP0 tiene que seguir al del
  CVA6). Además permite frecuencias que el PS no da, por ejemplo 95 MHz.
- Lo único probado en este eje fue `-clock_opt` post-route, sin efecto.

### 3. Sacar ILA y VIO del build de timing

Menos lógica y menos congestión alrededor del bus AXI. Ganancia probablemente
chica (0–0,1 ns, no medida) y se pierde la depuración en placa.

### 4. Excepciones de timing sobre los CSR (no recomendado)

- Las escrituras a `satp` vacían el pipeline (`flush_o = 1` en `csr_regfile.sv`).
- Las escrituras a `pmpcfg`/`pmpaddr` **no** lo vacían.
- Un multicycle desde los registros PMP no se puede justificar sin una prueba
  formal de que ningún consumidor captura el valor en el ciclo siguiente. Sin esa
  prueba, sería aparentar el cierre.

## Balance para el grupo PMP, que define la respuesta

| Palanca | Ganancia en PMP |
|---|---|
| Retiming | 0 (medido en la KR260: 0 registros movidos; en la VC707 tampoco en `pmp`) |
| MMCM + raíz del reloj | incierta, plausible 0,05–0,2 ns |
| Sin ILA/VIO | 0–0,1 ns |
| Herramientas y optimización física | agotadas |
| **Necesario** | **0,541 ns** |

Aun sumando los mejores casos, PMP queda corto. Por eso 100 MHz sin tocar el
CVA6 es poco probable, aunque el retiming resuelva la FPU.

## Frecuencias que el PS puede dar sin reprogramar PLLs

Referencia de 33,333 MHz. IOPLL = 999,99 MHz; RPLL = 1066,66 MHz (verificado:
R5 a 533,33 MHz con divisor 2).

| Fuente | Divisor | Frecuencia | Período | Estado |
|---|---:|---:|---:|---|
| IOPLL | 10 | 100,00 MHz | 10,000 ns | no cierra (−0,553 ns) |
| RPLL | 11 | 96,97 MHz | 10,313 ns | no probado |
| IOPLL | 11 | 90,91 MHz | 11,000 ns | **cerrado** (+0,001 ns) |
| RPLL | 12 | 88,89 MHz | 11,250 ns | no hace falta |
| IOPLL | 12 | 83,33 MHz | 12,000 ns | margen ~1 ns |

- 96,97 MHz se elige con `PL0_REF_CTRL__SRCSEL = RPLL`. El RPLL no cambia, así
  que no afecta al R5, SDIO ni SPI.
- Para cerrar, PMP necesita ≤ ~10,31 ns. El mejor valor medido a 100 MHz fue
  10,54 ns, así que también requiere que el clock o el retiming aporten.
- 95 MHz necesita un MMCM o reprogramar el RPLL (que alimenta R5, SDIO y SPI).

## Qué habría que modificar en el CVA6 para 100 MHz

Origen y destino de los caminos que fallan (mejor checkpoint a 100 MHz):

| Familia | Falta | Desde | Hacia |
|---|---:|---|---|
| PMP | 0,541 ns | `csr_regfile/pmpaddr_q` | caché de datos (421), LSU (63), scoreboard (37) |
| FPU CAST | 0,553 ns | registro intermedio de `fpnew_cast_multi` | `issue_read_operands` (178), scoreboard (53) |
| FPU FMA | 0,529 ns | registro intermedio de `fpnew_fma` | interior de la FPU (165) |
| Caché | 0,429 ns | write buffer de la D-cache | D-cache |
| MMU/TLB | 0,266 ns | tags de la TLB (`asid`) | I-cache |
| Operandos | 0,240 ns | `fu_data_q.operand_a` | LSU |

### PMP: precalcular la decodificación al escribir el CSR (sin cambio de comportamiento)

El peor camino PMP pasa primero por **6 niveles de LUT (~2,1 ns) que dependen
sólo de `pmpaddr`/`pmpcfg`**, antes de mezclarse con la dirección de memoria.
En `core/pmp/src/pmp_entry.sv` cada entrada recalcula en cada ciclo, a partir
del CSR, un `lzc` de 56 bits, la máscara NAPOT (`'1 << size`) y la base.

- Cambio: calcular esa máscara/base a partir del valor nuevo del CSR
  (`pmpaddr_d`/`pmpcfg_d`) y guardarla en registros que se actualizan en el
  mismo flanco que `pmpaddr_q`. El comportamiento ciclo a ciclo es idéntico.
- Por qué la herramienta no lo hace sola: `pmpaddr` y `pmpcfg` tienen
  habilitaciones de escritura distintas, y el retiming no puede mover registros
  con distinto control a través de la misma lógica.
- Efecto estimado: sacar ~2 ns de un camino al que le faltan 0,54 ns.
- Impacto: cambio de RTL en `csr_regfile`/`pmp`, sin cambio de latencia ni de
  microarquitectura (no afecta a gem5). Requiere simulación con pruebas de PMP.
- Alternativa de configuración: bajar `NrPMPEntries` (hoy 8). Reduce la
  decodificación y la cadena de prioridad, pero deja menos regiones PMP al
  software y probablemente gane menos.

### FPU (CAST y FMA)

`fpu_wrap.sv` usa `PipeConfig: DISTRIBUTED`, con `LAT_CONV = 2` y
`LAT_COMP_FP64 = 3` (`ariane_pkg.sv`).

- Sin tocar RTL: sintetizar con el reloj sobre-restringido (por ejemplo
  8,5–9 ns, sólo en síntesis) para que el retiming vea la FPU fallando y
  reubique sus registros, como pasó en la VC707. Ganancia incierta.
- Con cambio de RTL: una etapa más (`LAT_CONV` 2→3, `LAT_COMP_FP64` 3→4).
  Es la solución más segura, pero suma 1 ciclo a conversiones y FMA y hay que
  reflejarlo en gem5.
- Cambiar `PipeConfig` no ayuda: ya está distribuido.

### Familias menores (caché, MMU, operandos: faltan 0,24–0,43 ns)

Pueden cerrar solas cuando PMP y FPU dejen de competir por ubicación y ruteo,
pero no está garantizado. Si no:

- `InstrTlbEntries`/`DataTlbEntries` 16→8: TLB más chica (MMU, operandos).
- `DcacheSetAssoc` 8→4: comparación de tags más corta (caché).
- `FpgaEn = 1`: banco de registros y SRAM orientados a FPGA (operandos).

Las tres primeras cambian la microarquitectura y el rendimiento (afectan gem5).

### Orden sugerido

1. Precalcular PMP + síntesis sobre-restringida con retiming para la FPU. Una
   corrida a 100 MHz para medir lo que queda.
2. Si la FPU sigue fallando: +1 etapa en CAST/FMA.
3. Si quedan caché/MMU/operandos: decidir TLB/asociatividad en equipo.

Cada corrida completa lleva ~2 h; cada cambio de RTL requiere simulación previa.

## Recomendación

1. **Probar 90,9 MHz en placa primero.** Sin eso, todo lo demás es teórico.
2. El experimento con retiming ya se hizo y no aplicó (ver arriba). Con eso,
   **100 MHz sin tocar el CVA6 queda descartado en la práctica**: ninguna palanca
   medida ni plausible le da 0,54 ns al grupo PMP.
3. Si el proyecto necesita más de 90,9 MHz, hay que modificar el CVA6. El primer
   paso (precalcular la decodificación PMP) no cambia el comportamiento ni afecta
   a gem5; los siguientes (latencia de la FPU, TLB, asociatividad) sí, y conviene
   decidirlos en equipo. Ver "Qué habría que modificar en el CVA6 para 100 MHz".
4. No seguir con la campaña de micro-optimizaciones post-route a 100 MHz: mejoró
   el TNS pero no movió el WNS en ninguno de sus últimos ensayos.

## Fuentes de los datos

- Campaña a 100 MHz: `timing-preparation/focused_physical_20261021/night_run_20261021/runs/009_restruct_SATP/`
  (`all_failing_setup.tsv`, `critical_setup.rpt`) y `diagnostic_census_20261021/INFORME_ACTUAL.txt`.
- Cierre a 90,9 MHz: `timing-preparation/pl0_91mhz_20261022/` y el paquete congelado.
- Retiming en VC707: `logs/vc707_fpga_run2_20260729-014100.log` (Synth 8-5816).
- Retiming en KR260: `timing-preparation/exp100_retiming_20261022/` (`exp100*.log`,
  `synth_estimate/families.txt`) y el log de `synth_2` del proyecto.
- PLLs del PS: `.xci` de `kr260_ps_ddr_bd_zynq_ultra_ps_e_0_0`.
