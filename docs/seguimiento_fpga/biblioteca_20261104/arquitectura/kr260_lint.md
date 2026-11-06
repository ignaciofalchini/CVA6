# Lint Verilator y comprobaciones RTL del port KR260

Fecha: 2026-08-16
Commit: `57e2a6cdc0f0f2f3403b2918407832be49d08993`
Baseline: `cd7ab551783cdcbfc4c5f6fd954924c34074f14a`

## Estado

Respuesta a la pregunta de regresión RTL: `NO`.

Verilator 5.050 completó el análisis de `ariane_kr260`, de `cva6` actual y
baseline, y del sistema estructural sin crash ni error RTL del port. Los
warnings potencialmente funcionales son idénticos al baseline o provienen de
fuentes heredadas sin cambios.

La corrida anterior con Verilator 5.020 permanece documentada como
`INCONCLUSIVE`: no pudo terminar `V3Param` por un `SIGSEGV` de la herramienta.

El análisis detallado y todos los conteos están en
`reports/kr260_lint/FINAL_LINT_REPORT.md`.

## Herramientas

- Actual: `/home/nachofalchi/tools/verilator/bin/verilator`.
- Actual: `Verilator 5.050 2026-07-01 rev v5.050`.
- Corrida histórica: `/usr/bin/verilator`.
- Corrida histórica: `Verilator 5.020 2024-01-01 rev (Debian 5.020-1)`.
- `verible-verilog-lint` no está disponible; no se instaló nada.

## Infraestructura reutilizada

Se inspeccionaron `core/Flist.cva6`, el flujo Verilator del Makefile,
`Bender.yml`, `util/flist_flattener.py`, los Makefiles FPGA y los Tcl de Vivado.
La lista final no se construyó a mano: se reutilizó
`reports/kr260_next_steps/lint/kr260_xvlog.f`, exportada tras
`update_compile_order` por `corev_apu/fpga/scripts/run_kr260_lint.tcl`.

La lista contiene 247 archivos HDL ordenados para síntesis. Se usaron estos
includes:

```text
vendor/pulp-platform/common_cells/include
vendor/pulp-platform/axi/include
core/cache_subsystem/hpdcache/rtl/include
corev_apu/register_interface/include
core/include
```

No se necesitó `-DXLEN=64`: la configuración proviene de
`cv64a6_imafdc_sv39_config_pkg.sv`, con `CVA6Cfg` construido por el wrapper.
Esto corresponde al target `cv64a6_imafdc_sv39`, `XLEN=64`, `BOARD=kr260`.

## Comando principal

La primera pasada no usó `-Wno-*`, `lint_off`, waivers ni
`verilator_config.vlt`:

```sh
verilator --lint-only --no-timing -Wall \
  --top-module ariane_kr260 \
  --Mdir /tmp/cva6_kr260_lint_minimal_57e2a6cdc \
  -Ivendor/pulp-platform/common_cells/include \
  -Ivendor/pulp-platform/axi/include \
  -Icore/cache_subsystem/hpdcache/rtl/include \
  -Icorev_apu/register_interface/include \
  -Icore/include \
  -f reports/kr260_next_steps/lint/kr260_xvlog.f
```

El log completo está en
`reports/kr260_lint/verilator_ariane_kr260.log`.

## Cobertura

- `ariane_kr260`: lista completa de 247 fuentes; Verilator emitió warnings
  tempranos y luego sufrió `SIGSEGV` en `V3Param`.
- `ariane_kr260_debug`: misma lista más el wrapper debug. ILA/VIO sólo existen
  como DCP Vivado; no se inventaron stubs. La pasada aislada identifica
  exactamente esos módulos como no disponibles.
- `ariane_kr260_system`: misma lista más el RTL/netlist real del BD, los stubs
  de síntesis existentes del PS/reset, el wrapper BD y el wrapper propio. El
  comportamiento propietario del PS/DDR no está modelado por esos stubs.
- `cva6`: pasada profunda completada tras suprimir solamente
  `BLKANDNBLK`, una vez demostrado que sus 50 instancias son idénticas al
  baseline y que el Makefile histórico ya suprime esa regla.

Logs principales:

- `reports/kr260_lint/verilator_ariane_kr260.log`;
- `reports/kr260_lint/verilator_kr260_debug.log`;
- `reports/kr260_lint/verilator_kr260_system.log`;
- `reports/kr260_lint/verilator_baseline.log`.

## Baseline

El commit baseline se abrió en un worktree detached temporal; el working tree
actual no se cambió. Con top `cva6`, actual y baseline tienen exactamente:

- 50 `BLKANDNBLK` raw;
- 33 `LATCH`;
- 24 `UNDRIVEN`;
- 28 `UNOPTFLAT` en la pasada profunda;
- 229 `WIDTHEXPAND`;
- 75 `WIDTHTRUNC`;
- los mismos avisos de rangos, signed/unsigned y reset.

El wrapper baseline `ariane_xilinx` también muestra cuatro `PINMISSING` de
`axi2mem`, 11 `WIDTHCONCAT` y el mismo fallo interno. `ariane_kr260` muestra
cuatro `PINMISSING` equivalentes y seis `WIDTHCONCAT`.

## Diagnósticos propios del port

- Diez `PINCONNECTEMPTY` en `ariane_kr260.sv`: salidas deliberadamente
  descartadas de reset, DMI/JTAG, adapter, RVFI y ROM.
- Cuatro `PINMISSING` `user_i/user_o` en dos `axi2mem`: la misma omisión existe
  en el wrapper FPGA del baseline.
- Verilator 5.020 emitía seis `WIDTHCONCAT` en `AXI_XBAR_CFG`. Verilator
  5.050 ya no los emite sin que se haya modificado ese RTL.
- Cuatro `PINMISSING` adicionales del sistema: salidas no usadas de
  `proc_sys_reset` en el netlist generado por Vivado.
- El RTL propio debug/system no emitió warnings de ancho, driver, latch o loop
  en la corrida 5.050.

No se observaron `MULTIDRIVEN` ni `CASEOVERLAP`. Los tres `CASEINCOMPLETE` de
5.050 están en el `axi2mem.sv` heredado: estados inválidos y el AXI BURST
reservado `2'b11`. Los `LATCH`, `UNDRIVEN`, `UNOPTFLAT`, `WIDTHEXPAND` y
`WIDTHTRUNC` del núcleo tienen conteos idénticos al baseline.

## AXI, memoria y debug

La frontera `m_axi_mem_*` conecta todos los canales AW/W/B/AR/R y conserva
READY/VALID. Los IDs CVA6 de 5 bits se extienden a 6 bits con cero para
HP0_FPD; BID/RID se reducen a `[4:0]` con assertions sobre el bit alto. USER se
fuerza a cero en el PS y retorna cero; ATOP se consume antes de la frontera y
se verifica cero. La dirección resta `0x8000_0000` antes de seleccionar
`[48:0]`, con assertions que limitan el tráfico a la ventana válida de 1 GiB.

No hay evidencia de un truncamiento silencioso válido, pérdida de ID,
desconexión READY/VALID ni señal `m_axi_mem_*` abandonada. Verilator sólo cubre
la conectividad estructural del PS/DDR, no el comportamiento interno de la IP.
En debug, `dmi_rst_no` y `tdo_oe_o` son salidas deliberadamente no usadas; ILA
y VIO quedan fuera de elaboración por ser DCP.

## Verilator 5.050

- Versión: `Verilator 5.050 2026-07-01 rev v5.050`, ejecutada desde
  `/home/nachofalchi/tools/verilator/bin/verilator`.
- Se repitieron los comandos 5.020 con los mismos tops, filelists, includes,
  defines y fuentes; sólo se sustituyeron el ejecutable y `--Mdir`.
- No se usaron `-Wno-*`, `lint_off`, waivers ni modelos falsos.

Resultados:

- `ariane_kr260` completó el análisis sin crash ni error RTL y terminó al final
  por 1321 warnings fatales de `-Wall`.
- El `cva6` baseline completó sin crash ni error RTL con 1230 warnings. El
  `cva6` actual produjo 1244; las únicas diferencias son los 10
  `PINCONNECTEMPTY` y cuatro `PINMISSING` del wrapper presente sólo en el
  filelist actual. `LATCH` (23), `UNDRIVEN` (24), `UNOPTFLAT` (2),
  `WIDTHEXPAND` (213) y `WIDTHTRUNC` (75) son idénticos.
- El wrapper baseline `ariane_xilinx -DGENESYSII` es rechazado por 5.050 antes
  de elaborar: la rama histórica deja una coma final en la lista de parámetros.
  Es un error preexistente del baseline que 5.020 aceptaba, no un error KR260.
- `ariane_kr260_debug` llegó hasta dos `MODMISSING` esperados:
  `kr260_axi_ila` y `kr260_reset_vio`. Sólo existen como DCP y no se crearon
  stubs.
- `ariane_kr260_system` completó el análisis estructural con 1658 warnings y
  sin error RTL propio. Los 18 `UNDRIVEN` adicionales pertenecen exclusivamente
  a los stubs de síntesis PS/reset; no hay modelo funcional propietario de
  PS/DDR.

Warnings nuevos observables con 5.050:

- tres `CASEINCOMPLETE` en el `axi2mem.sv` heredado: estados codificados
  inválidos y AXI BURST reservado `2'b11`;
- un `SYNCASYNCNET` adicional sobre el reset del wrapper, cuya ruta síncrona
  señalada es el `disable iff` de una assertion y no un segundo driver;
- dos `UNUSEDSIGNAL` de `ps_awaddr_translated[63:49]` y
  `ps_araddr_translated[63:49]`, esperados por la selección explícita `[48:0]`
  posterior a la traducción y protegida por assertions de rango.

Estos warnings no son evidencia de regresión: `axi2mem`, `axi_riscv_lrsc`,
`dm_top` y `rstgen_bypass` son idénticos al baseline. No hay `BLKANDNBLK`,
`MULTIDRIVEN`, `WIDTHCONCAT` ni warning de ancho/driver/latch/loop en los
wrappers KR260. Fuera de esos dos `UNUSEDSIGNAL`, tampoco hay diagnóstico
nuevo sobre `m_axi_mem_*`, IDs, USER, ATOP, READY/VALID o la traducción de
direcciones.

Respecto de 5.020, desapareció el `SIGSEGV` de `V3Param` y el top principal
llegó al final sin suprimir warnings. 5.050 dejó de reportar los 50
`BLKANDNBLK` y los seis `WIDTHCONCAT`; además cambió conteos de `LATCH`,
`UNOPTFLAT`, `ASCRANGE` y `WIDTHEXPAND` de forma igual en actual y baseline.
Los logs completos están en `reports/kr260_lint/verilator_505_*.log`.

## Correcciones y límites

No se encontró un problema nuevo inequívoco y no se modificó RTL. Por ello no
correspondía repetir `xvlog`, elaboración RTL o synthesis-only como validación
de un fix, ni crear un commit. La compilación/elaboración Vivado previa sigue
documentada: `xvlog` procesó 247 archivos sin errores ni warnings y los tres
wrappers habían sido sintetizados sin errores ni black boxes inesperadas.

El cambio preexistente en `corev_apu/fpga/src/ariane_xilinx.sv` permaneció
intacto. No se ejecutó Implementation, Bitstream ni `git push`.

## Conclusión

> ¿El lint encontró evidencia de que el port a KR260 haya roto RTL que antes era válido?

`NO`

Verilator 5.050 completó `ariane_kr260`, ambos núcleos comparables y el sistema
estructural sin crash ni error RTL del port. Los diagnósticos funcionales son
idénticos al baseline o heredados, y no hay warning nuevo sobre la frontera
AXI/memoria. La ausencia de modelos funcionales ILA/VIO/PS/DDR limita esa IP
propietaria, pero no aporta evidencia de que KR260 haya roto RTL antes válido.
