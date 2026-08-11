# Resultado

SUCCESS — la síntesis de KR260 terminó correctamente. No se ejecutó implementación ni se generó bitstream.

# Baseline

- Rama original: `vc707-ignacio`
- SHA original: `cd7ab551783cdcbfc4c5f6fd954924c34074f14a`
- El cambio preexistente en `corev_apu/fpga/src/ariane_xilinx.sv` se preservó sin modificar.
- No se modificó ningún archivo de `core/`; no hubo cambios de microarquitectura, ISA ni XLEN.

# Rama de trabajo

`kr260-port`, creada desde el SHA de baseline. No se realizaron commits locales; `HEAD` sigue en el SHA de baseline.

# KR260 detectada

La identificación se consultó en la instalación real de Vivado 2026.1:

- `XILINX_PART=xck26-sfvc784-2LV-c`
- `XILINX_BOARD=xilinx.com:kr260_som:part0:2.0`
- Board parts encontrados: `xilinx.com:kr260_som:part0:1.0`, `1.1` y `2.0`.
- Parte asociada al board part 2.0: `xck26-sfvc784-2LV-c`.

# Arquitectura antes

El wrapper VC707 `ariane_xilinx.sv` combina CVA6, crossbar AXI, bootrom, CLINT, debug/JTAG, periféricos, conversión de clocks y controladores de memoria de varias placas. En VC707, la región DRAM `0x8000_0000..0xBFFF_FFFF` atraviesa atomics y un conversor AXI de clock hasta `xlnx_mig_7_ddr3`.

El análisis completo y la clasificación por bloques están en `docs/kr260_port_analysis.md`. El seguimiento LSU a DDR y la frontera propuesta están en `docs/kr260_memory_path.md`.

# Qué se eliminó del wrapper KR260

- `xlnx_mig_7_ddr3`, su reloj UI y el conversor AXI asociado: son IP DDR3 de serie 7 y no describen la DDR del MPSoC KR260.
- Controlador DDR4 de VCU118 y selección multiboard: ajenos a KR260.
- Generación de clocks MMCM/IP específica de VC707 y el clock derivado de MIG.
- Ethernet, SPI/SD, GPIO, LEDs, switches, fan y UART/APB: no son necesarios para el primer sistema mínimo y no se instancian.
- PLIC y timer APB: se eliminan junto con los periféricos no esenciales.
- Constraints de VC707: no se reutilizan.

`ariane_xilinx.sv` y su flujo VC707 quedan como baseline y no fueron modificados por este port.

# Qué se conservó

- CVA6 `cv64a6_imafdc_sv39`, XLEN=64, caches, MMU, FPU y toda la microarquitectura.
- Bootrom `bootrom_64` mapeada en `0x0001_0000`.
- CLINT y crossbar AXI para ROM, CLINT, debug y DRAM.
- `axi_riscv_atomics_wrap`, por lo que AMO/LR/SC siguen presentes antes de la salida de memoria.
- Debug RISC-V y DMI/JTAG, expuestos como puertos lógicos sin asignar pines.
- Reset limpio mediante `rstgen`: reset externo y `ndmreset` de debug.
- Clock de CVA6 de entrada `clk_i`, con constraint de 40 ns.

# Wrapper KR260

`corev_apu/fpga/src/ariane_kr260.sv` es un top separado, sin ifdefs de placa. Su top-level expone:

- `clk_i` y `rst_ni`;
- JTAG opcional;
- `m_axi_mem_*`, AXI4 explícito hacia la memoria futura: dirección y datos de 64 bits, IDs de 5 bits y USER de 64 bits.

Esto mantiene visible la integración y evita cualquier controlador DDR inventado.

# Camino a memoria

La frontera resultante es:

```
CVA6 LSU → caches → NOC AXI de ariane → axi_xbar_intf
→ axi_riscv_atomics_wrap → m_axi_mem_* AXI4
→ [futuro puente PS/PL hacia la memoria DDR de KR260]
```

No existe memoria falsa ni MIG heredado. Falta elegir y diseñar explícitamente el puente real: PS HP/HPC/NoC, clocks/reset, adaptación de ancho/IDs/ATOP y mapa de memoria/boot firmware.

# Archivos modificados o agregados

- `Makefile`: añade `BOARD=kr260`, part, board part, `CLK_PERIOD_NS=40` y excluye fuentes VC707 del target KR260.
- `corev_apu/fpga/Makefile`: objetivo synthesis-only `kr260-synth`; no define implementación ni bitstream para KR260.
- `corev_apu/fpga/src/ariane_kr260.sv`: wrapper mínimo nuevo.
- `corev_apu/fpga/constraints/kr260.xdc`: sólo `create_clock -period 40.000 [get_ports clk_i]`; no hay pines inventados.
- `corev_apu/fpga/scripts/run_kr260_synth_2.tcl`: proyecto separado `ariane_kr260`, `set_param general.maxThreads 1`, `launch_runs synth_1 -jobs 1`, reportes, control de black boxes y DCP.
- `docs/kr260_port_analysis.md` y `docs/kr260_memory_path.md`.

# Linter

`verible-verilog-lint` y `verilator` no están instalados localmente. No se instalaron herramientas nuevas.

Como comprobación de integración se ejecutó `synth_design -rtl` antes de `synth_1`; completó correctamente. La síntesis completa posterior confirmó sintaxis, elaboración, puertos y anchos de la integración.

# Síntesis

Comando de éxito:

```
make fpga BOARD=kr260 target=cv64a6_imafdc_sv39 KR260_ATTEMPT=2
```

Vivado 2026.1 usó un único `synth_1`, con `general.maxThreads=1` y `-jobs 1`.

| Intento | Duración | Estado | Causa / resultado |
| --- | ---: | --- | --- |
| 1 | 11 s | Fallido | Error del script al intentar aplicar propiedades a un header que no era objeto del fileset; no llegó a elaborar RTL. Log archivado. |
| 2 | 18 min 59 s | Exitoso | `synth_design Complete!`; elaboración, síntesis, reportes y DCP completados. |

Resultado del intento 2:

- `0 errors`, `0 critical warnings`.
- 300 warnings en el resumen de síntesis; 527 advertencias totales del log. Las relevantes son señales AXI sideband no consumidas por `axi2mem`, optimizaciones internas preexistentes del core y E/S físicas aún no definidas. No hay black boxes remanentes.
- Utilización: 57 521 LUT, 28 877 FF, 38 RAMB36, 0 RAMB18, 27 DSP.
- El hierarchy report conserva `i_ariane/i_cva6`: 50 842 LUT, 23 558 FF, 36 RAMB36 y 27 DSP. El diseño no fue optimizado hasta quedar vacío.
- Clock `cva6_clk`: período 40.000 ns (25 MHz), WNS de setup 29.744 ns y ningún endpoint de setup fallido en post-síntesis.
- Hay hold WNS de -0.033 ns y 7 482 endpoints de hold en netlist sintetizada, además de 258 registros de JTAG sin clock físico y E/S sin input/output delay. Se conservan como pendientes físicos: no se aplicaron falsos paths ni constraints ficticios.
- DCP válido generado por Vivado: `reports/kr260_port/attempt_2/ariane_kr260_synth.dcp` (30 183 145 bytes).
- Reportes: `ariane_kr260.utilization.rpt`, `ariane_kr260.timing_summary.rpt`, `ariane_kr260.check_timing.rpt`, `ariane_kr260.blackboxes.rpt` y logs por intento.

# Diferencias contra VC707

VC707 conserva MIG DDR3, clocks dependientes del MIG, constraints y periféricos de la placa. KR260 usa el device/board part reales de Zynq UltraScale+, clock de entrada de 25 MHz y una frontera AXI externa; no reutiliza IP DDR3, clocks ni pines de VC707.

# Estado de preparación

- **Synthesis-ready: sí.** El wrapper KR260, el target Make, constraint de 40 ns y DCP sintetizado están validados.
- **Implementation-ready: no.** Faltan la integración PS/PL, top con pines reales, clocks JTAG/memoria, delays de E/S y resolución de los hold paths con netlist colocado/ruteado.
- **Hardware-ready: no.** No existe aún conexión física a DDR de KR260, boot firmware compatible con el mapa final, ni constraints de hardware. No se debe inferir funcionamiento en placa de esta síntesis.

# Próximos pasos recomendados

1. Elegir la arquitectura PS/PL para conectar `m_axi_mem_*` a la DDR del KR260 y definir sus clocks/resets.
2. Añadir el wrapper de sistema/pines reales y constraints verificables; luego ejecutar implementación.
3. Adaptar y probar bootrom/software contra el mapa de memoria definitivo.
4. Agregar ILA/VIO recién después de estabilizar memoria y arranque.
