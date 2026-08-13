LINTER: PARTIAL
ILA: SUCCESS
VIO: SUCCESS
BOOTROM TEST: SUCCESS
MEMORY ARCHITECTURE: SUCCESS
PS/DDR PROTOTYPE: SUCCESS
SYNTHESIS: SUCCESS

# Informe final: siguientes pasos del port CVA6 a KR260

Este resultado deja tres variantes separadas: el top mínimo, un wrapper de
debug con ILA/VIO y un prototipo de sistema que conecta la frontera AXI de CVA6
al puerto HP0 del Processing System. No se ejecutó implementación ni se generó
bitstream. “SUCCESS” en bootrom y PS/DDR significa que el artefacto fue
preparado, validado y sintetizado dentro del alcance de esta tanda; no significa
que haya funcionado todavía sobre DDR física.

## 1. Linter

No se encontraron Verible, Verilator, Slang ni Icarus instalados. Sí están
Vivado 2026.1 y su frontend `xvlog`. Por eso el estado es `PARTIAL` y no se
instaló ni descargó ninguna herramienta.

La comprobación secundaria reprodujo las fuentes, includes y configuración
`cv64a6_imafdc_sv39`:

- `xvlog`: 247 archivos, 0 errores y 0 warnings;
- `synth_design -rtl`: 0 errores, 0 critical warnings, 327 warnings y 0 black
  boxes inesperadas;
- los wrappers de debug y sistema compilaron y pasaron sus síntesis completas.

Los warnings funcionalmente atendibles (`nets` sin driver y registros
recortados) están en módulos preexistentes de PTW/MMU/load unit/CLINT, no en el
wrapper KR260. El resto corresponde principalmente a puertos genéricos sin uso,
parámetros de packages y estilo de herramienta. No se cambió RTL para satisfacer
estilo. La clasificación y los comandos exactos están en `docs/kr260_lint.md`.

Queda pendiente ejecutar un linter dedicado, idealmente Verilator
`--lint-only` y Verible, cuando exista una instalación local confiable.

## 2. ILA

`ariane_kr260_debug.sv` envuelve `ariane_kr260`; el top mínimo permanece limpio
y sintetizable sin IP de debug. El ILA real de Vivado usa `clk_i`, profundidad
2048 y nueve probes agrupadas:

- lectura: ARADDR, ARVALID/READY/LEN/SIZE, RDATA y
  RVALID/READY/RESP/LAST;
- escritura: AWADDR, AWVALID/READY/LEN/SIZE, WDATA,
  WSTRB/VALID/READY/LAST y BRESP/VALID/READY.

Esto permite ver dirección, datos, tamaño/burst, handshake y respuesta sin
capturar señales internas de la microarquitectura. Para una lectura se espera
un handshake AR, uno o más beats R y `RLAST`; para una escritura se esperan los
handshakes AW y W —que AXI permite desacoplar— seguidos de B. Una respuesta
normal tiene `RRESP/BRESP=OKAY`.

El ILA consume 1.587 LUT, 2.667 FF y 17 RAMB36. El mapa bit a bit y los triggers
sugeridos están en `docs/kr260_ila_vio.md`.

## 3. VIO

El VIO observa `rst_ni` y el reset efectivo `core_rst_ni`. Su única salida es
`soft_reset`, inicializada en cero y combinada así:

```systemverilog
assign core_rst_ni = rst_ni & ~soft_reset;
```

Sólo puede agregar reset; nunca puede anular el reset externo. No controla AXI
ni simula memoria, y existe únicamente en el wrapper debug. Consume 103 LUT y
250 FF.

Al abrir `ariane_kr260_debug/ariane_kr260_debug.xpr`, ambos IP aparecen en
**Sources → IP Sources**. Después de abrir el diseño sintetizado,
`get_debug_cores` encuentra ILA y VIO. Hardware Manager recién podrá usarlos
cuando una etapa futura genere e instale un bitstream.

## 4. Bootrom

Se creó una variante RV64 bare-metal opt-in bajo
`corev_apu/fpga/src/bootrom/kr260_memory_test/`. La ROM normal sigue siendo el
default. La prueba:

1. escribe `0xa55a_a55a_dead_beef` en `0x8000_0000`;
2. ejecuta `fence`, vuelve a leer y compara;
3. si coincide, escribe repetidamente `0x600d_600d_600d_600d` en
   `0x8000_0008`;
4. si falla, escribe repetidamente `0xbad0_bad0_bad0_bad0` en
   `0x8000_0010`.

No usa UART, GPIO, sistema operativo ni runtime. El ELF es RV64 little-endian,
entrada `0x10000`, atributo ISA `rv64im_zicsr`; el binario mide 148 bytes. El
flujo existente generó ELF, bin, imagen, módulo SV, header y disassembly. La
ROM compiló con `xvlog` y elaboró tanto seleccionada como deseleccionada.

En ILA, el primer store debe mostrar `AWADDR=0x8000_0000`,
`WDATA=0xa55a...beef`, `WSTRB=ff` y `BRESP=OKAY`. La lectura puede ser un burst
de fill de cache; debe localizarse el beat que contiene el patrón. Los stores
repetidos a `+8` o `+16` distinguen éxito y error. Esto todavía no se observó en
hardware.

## 5. Memoria: camino CVA6 → DDR

El camino recomendado y prototipado es:

```text
CVA6 RV64
  ↓
I/D caches + MMU + FPU
  ↓
AXI crossbar
  ↓
axi_riscv_atomics_wrap
  ↓
m_axi_mem_* (addr64/data64/id5/user64 estructural)
  ↓
adaptador explícito (dirección, ID, USER, ATOP/LOCK)
  ↓
S_AXI_HP0_FPD (AXI4 addr49/data64/id6, no coherente)
  ↓
interconnect + controlador/PHY DDR del PS
  ↓
DDR4 del K26 SOM
```

La ventana CVA6 `0x8000_0000..0xbfff_ffff` se traduce restando
`0x8000_0000` a la ventana física PS `0x0000_0000..0x3fff_ffff`. Así se usa el
GiB inferior de `DDR_LOW` sin tocar la reserva PMU
`0x7ff0_0000..0x7fff_ffff`.

Los datos y bursts son AXI4 de 64 bits en ambos lados. Los IDs se extienden
5→6 con cero y se comprueba que la respuesta conserve el bit alto en cero.
USER está deshabilitado en la configuración CVA6: se comprueba/corta y el PS
recibe cero. `axi_riscv_atomics_wrap` convierte AMO/LR-SC antes de esta frontera;
el wrapper verifica en simulación que ATOP y LOCK ya sean cero.

No se necesita SmartConnect, Data Width Converter, Protocol Converter ni Clock
Converter en este caso uno-a-uno, de igual ancho y clock. La evidencia y las
alternativas HP/HPC están en `docs/kr260_ps_ddr_architecture.md`.

## 6. PS/PL

Pertenece al Programmable Logic:

- CVA6, caches, MMU, FPU, bootrom, CLINT, debug y crossbar;
- el wrapper de atomics;
- la adaptación de dirección, ID y sidebands;
- ILA/VIO en la variante debug.

Pertenece al Processing System Zynq UltraScale+:

- la terminación `S_AXI_HP0_FPD` y su interconnect interno;
- el controlador y PHY de DDR;
- la configuración física DDR/MIO tomada del board preset;
- `pl_clk0` y `pl_resetn0` usados por el prototipo.

El Block Design solicita 25 MHz y Vivado reporta 24,999750 MHz. Ese clock
alimenta CVA6 y `saxihp0_fpd_aclk`; `proc_sys_reset` sincroniza la liberación del
reset. El PS necesita firmware de arranque que inicialice DDR y configure esa
secuencia antes de que el sistema pueda funcionar en placa.

## 7. Archivos creados o modificados

Port mínimo ya protegido en el commit inicial:

- `corev_apu/fpga/src/ariane_kr260.sv` y su target de síntesis;
- constraints mínimos de clock, análisis e informe previos.

Lint:

- `corev_apu/fpga/scripts/run_kr260_lint.tcl`;
- `docs/kr260_lint.md`.

Debug:

- `corev_apu/fpga/src/ariane_kr260_debug.sv`;
- `corev_apu/fpga/scripts/create_kr260_debug_ips.tcl`;
- `corev_apu/fpga/scripts/run_kr260_debug_synth.tcl`;
- `docs/kr260_ila_vio.md`;
- nuevos targets reproducibles en `corev_apu/fpga/Makefile`.

Bootrom:

- `corev_apu/fpga/src/bootrom/kr260_memory_test/{memory_test.S,linker.lds,Makefile,.gitignore}`;
- `corev_apu/fpga/scripts/select_kr260_memory_test_bootrom.tcl`;
- selección opt-in en `ariane_kr260.sv` y scripts de comprobación;
- `docs/kr260_bootrom_memory_test.md`.

Memoria PS/DDR:

- `corev_apu/fpga/scripts/inspect_kr260_ps_interfaces.tcl`;
- `docs/kr260_ps_ddr_architecture.md`;
- `corev_apu/fpga/src/ariane_kr260_system.sv`;
- `corev_apu/fpga/scripts/create_kr260_ps_ddr_bd.tcl`;
- `corev_apu/fpga/scripts/run_kr260_system_synth.tcl`;
- target `kr260-system-synth` en `corev_apu/fpga/Makefile`.

Este informe está en `reports/kr260_next_steps/FINAL_REPORT.md`. Los proyectos,
IPs generados, DCP y logs permanecen como artefactos regenerables no
versionados. El cambio preexistente de `ariane_xilinx.sv` fue preservado y no
se incluyó en ningún commit de esta tanda.

## 8. Commits locales

Los commits funcionales, separados en orden, son:

```text
b74d07155 fpga: add minimal KR260 synthesis target
3006d2364 fpga: add KR260 RTL lint checks
cb6b8f40b fpga: add KR260 ILA and VIO debug wrapper
eb8d19ffb fpga: add KR260 bootrom memory test
e9fe92486 docs: document KR260 PS DDR architecture
fde854d55 fpga: prototype KR260 PS DDR bridge
```

No se hizo squash ni push.

## 9. Síntesis

Todas las corridas usaron Vivado 2026.1, parte
`xck26-sfvc784-2LV-c`, board part `xilinx.com:kr260_som:part0:2.0`,
`general.maxThreads=1` y un solo job.

| Variante | Resultado | LUT | FF | RAMB36 | DSP |
| --- | --- | ---: | ---: | ---: | ---: |
| `ariane_kr260` mínima | 0 errores / 0 critical warnings | 57.521 | 28.877 | 38 | 27 |
| `ariane_kr260_debug` | 0 errores / 0 critical warnings | 59.245 | 31.794 | 55 | 27 |
| `ariane_kr260_system` + PS/HP0 + ROM test | 0 errores / 0 critical warnings | 57.779 | 28.854 | 36 | 27 |

El sistema integrado pasó en su primer intento completo
`validate_bd_design`, `generate_target`, síntesis y el chequeo de black boxes.
El reporte de configuración confirma HP0 addr49/data64/id6, USER de request de
1 bit, bursts de hasta 256 beats, 16 transacciones read/write outstanding y la
asignación física de 1 GiB desde cero. No hay black boxes inesperadas.

El timing sintetizado del sistema tiene `WNS=29,497 ns` pero
`WHS=-0,033 ns`. También quedan JTAG y sus I/O sin constraints de placa. Son
resultados pre-implementación; no se agregaron false paths, no se redujo ningún
DRC y no se ejecutó implementación.

La evidencia queda en `reports/kr260_next_steps/{lint,bootrom,debug,system_synth}/`.

## 10. Qué NO está demostrado todavía

### RTL correcto

Sí está demostrado que el RTL compila, elabora, conecta IP reales y sintetiza.
Las aserciones documentan los invariantes de la frontera. No hay simulación con
un modelo DDR que demuestre semántica ciclo a ciclo ni lint dedicado completo.

### Synthesis-ready

Sí: mínimo, debug y PS/DDR sintetizan. Esto no convierte automáticamente el
diseño en implementable o funcional.

### Implementation-ready

No está demostrado:

- no se ejecutaron opt/place/route ni DRC post-route;
- el hold estimado sólo puede evaluarse correctamente después del ruteo;
- falta decidir y documentar el routing físico JTAG antes de agregar pines;
- el ILA/VIO y PS/DDR son hoy tops separados; deben combinarse para captura
  sobre DDR real;
- no se generó una plataforma/boot image PS completa.

### Hardware-ready

No está demostrado:

- DDR no fue inicializada por FSBL/firmware y el test no corrió en la placa;
- falta reservar el GiB bajo para que APU/PMU y CVA6 no lo usen a la vez;
- no se observó tráfico real ni respuestas AXI en ILA;
- no se verificaron reset, clock, JTAG, temperatura ni margen físico;
- no existe bitstream por decisión explícita de esta tanda.

## 11. Qué debería revisar Ignacio para aprender

1. `corev_apu/fpga/src/ariane_kr260.sv`: seguir el SoC mínimo, el decode de
   memoria y la frontera `m_axi_mem_*`; observar que caches, MMU, FPU y atomics
   siguen presentes.
2. `corev_apu/fpga/src/ariane_kr260_debug.sv`: aprender a instrumentar un
   wrapper sin contaminar el top base, agrupar probes AXI y agregar un reset de
   debug seguro.
3. `corev_apu/fpga/scripts/create_kr260_debug_ips.tcl`: ver qué propiedades
   hacen reproducibles ILA/VIO y cómo sus XCI aparecen en IP Sources.
4. `corev_apu/fpga/src/bootrom/kr260_memory_test/memory_test.S`, seguido de
   `linker.lds` y `Makefile`: relacionar instrucciones RV64, direcciones y
   patrones con los handshakes que mostrará el ILA.
5. `corev_apu/fpga/scripts/inspect_kr260_ps_interfaces.tcl` y
   `docs/kr260_ps_ddr_architecture.md`: aprender a basar HP versus HPC y los
   anchos AXI en propiedades reales de Vivado/board files.
6. `corev_apu/fpga/src/ariane_kr260_system.sv`: estudiar la frontera más
   importante: traducción de dirección, adaptación de ID, descarte explícito
   de USER y contrato ATOP/LOCK.
7. `corev_apu/fpga/scripts/create_kr260_ps_ddr_bd.tcl`: seguir qué pertenece al
   PS, cómo se habilita HP0, cómo se asigna DDR_LOW y cómo se generan clock y
   reset sin inventar pines.
8. `corev_apu/fpga/scripts/run_kr260_system_synth.tcl`: ver el flujo completo
   reproducible —crear proyecto, generar BD, sintetizar, inspeccionar black
   boxes y emitir evidencia— sin Implementation ni Bitstream.

El siguiente hito técnico razonable es combinar el wrapper de debug con el
sistema PS/DDR, definir con evidencia el JTAG físico y preparar firmware PS
mínimo que inicialice DDR y libere PL. Recién entonces corresponde ejecutar
implementación y, en una etapa autorizada posterior, probar la bootrom en
hardware.
