# Análisis previo al port KR260

Fecha: 2026-08-10. Este documento se escribió antes de modificar el RTL de
integración. El baseline inspeccionado es `cd7ab551783cdcbfc4c5f6fd954924c34074f14a`
en la rama `vc707-ignacio`.

## Target detectado en la instalación de Vivado

La consulta Tcl de Vivado 2026.1 instalado localmente devolvió:

* `get_parts *xck26*`: `xck26-sfvc784-2LV-c`, `xck26-sfvc784-2LVI-i`.
* `get_board_parts *kr260*`: versiones `1.0`, `1.1` y `2.0` de
  `xilinx.com:kr260_som:part0`.
* El `board_part` 2.0 tiene `PART_NAME=xck26-sfvc784-2LV-c`,
  `DISPLAY_NAME=ROBOTICS SOM Evaluation Platform` y revisión `Rev_B01`.

Por tanto el port usará, de forma comprobada:

```text
XILINX_PART=xck26-sfvc784-2LV-c
XILINX_BOARD=xilinx.com:kr260_som:part0:2.0
CLK_PERIOD_NS=40
```

## Mapa de `ariane_xilinx.sv`

`ariane_xilinx.sv` es un único top multinivel y multiboard (1912 líneas).
Sus puertos se seleccionan con `GENESYSII`, `KC705`, `VC707`, `VCU118` y
`NEXYS_VIDEO`; por ello no es un buen punto para agregar otra rama grande de
`ifdef`.

| Bloque | Clasificación | Contenido y dependencia |
| --- | --- | --- |
| Puertos de placa, líneas 14–183 | ESPECIFICO_VC707 / COMUN_FPGA | Los puertos `sys_clk_p/n`, DDR3, RGMII, LEDs, switches, fan y JTAG se multiplican por placa. Para VC707 son pines físicos de serie 7 y no se pueden reutilizar para KR260. SPI, JTAG y UART están fuera del `ifdef`, aunque sus pines los fija cada XDC. |
| `build_fpga_config`, tipos AXI y buses, 188–250 | CORE / COMUN_FPGA | Conserva `cv64a6_imafdc_sv39`, AXI de 64 bits y dos iniciadores (CVA6 y debug). La configuración sólo ajusta reglas de no idempotencia para la región DRAM; no altera el microprocesador. |
| Reset y señales de clock, 251–321 | CLOCK/RESET | `rstgen` genera `ndmreset_n`; en VC707 `rst_n` procede de `ddr_sync_reset`, que a su vez es generado por MIG. El clock de CVA6 llega indirectamente desde la UI clock de MIG a `xlnx_clk_gen`, que produce 50 MHz. Esto es una dependencia que debe desaparecer en KR260. |
| Crossbar AXI, 324–372 | COMUN_FPGA / MEMORIA | `axi_xbar_intf` decodifica Debug, ROM, CLINT, PLIC, UART, Timer, SPI, Ethernet, GPIO y DRAM. CVA6 y el debug module son los dos iniciadores AXI; los destinos incluyen la ventana DRAM en `0x8000_0000`. |
| DMI/JTAG y debug module, 374–755 | DEBUG / COMUN_FPGA | `dmi_jtag`, `dm_top`, `axi2mem` y `axi_adapter` implementan RISC-V Debug. JTAG sólo se vuelve dependiente de VC707 al asignarle pines en el XDC; la lógica no depende de MIG ni de serie 7. |
| Instancia `ariane`, 757–794 | CORE | Instancia `ariane` con `CVA6Cfg`, arranque en `ariane_soc::ROMBase`, interrupciones y el puerto NOC AXI. `corev_apu/src/ariane.sv` instancia `cva6` sin cambiar configuración, pipeline, cachés, MMU ni ISA. |
| CLINT, 797–817 | PERIFERICO / COMUN_FPGA | Mantiene IPI y timer interrupt. Su RTC es un divisor por dos del clock de CVA6. Es el periférico mínimo que da la infraestructura de temporizador/soft interrupt al core. |
| ROM, 820–856 | MEMORIA / COMUN_FPGA | `axi2mem` convierte el destino AXI ROM y `bootrom_64` entrega el contenido generado. CVA6 comienza a fetchear desde `ROMBase=0x0001_0000`; este bloque debe conservarse. |
| `ariane_peripherals`, 858–920 | PERIFERICO | Integra PLIC, UART, SPI/SD, GPIO, Ethernet opcional y timer. VC707 habilita UART, GPIO y SPI, pero `InclEthernet=0`; aun así conserva puertos y clocks RGMII en el top. |
| Atómicos y bus DRAM, 931–1050 | MEMORIA / COMUN_FPGA | `axi_riscv_atomics_wrap` recibe el destino AXI DRAM y emite un AXI4 de 64 bits (`dram`). Este es el último punto común independiente de la tecnología de memoria. |
| AXI clock converter, 1052–1136 | ESPECIFICO_VC707 | Cruza el AXI de `clk` a `ddr_clock_out`, la UI clock de MIG. No es válido para la frontera KR260 porque la nueva memoria todavía no tiene clock ni protocolo de lado PL definidos. |
| `xlnx_clk_gen`, 1138–1164 | ESPECIFICO_VC707 | MMCM/IP pensado para recibir la UI clock del DDR controller y crear 50/125 MHz para SoC, Ethernet y SD. No debe sobrevivir en el top KR260. |
| `fan_ctrl`, 1165–1171 | ESPECIFICO_VC707 | PWM a fan de Kintex/VC707. |
| `xlnx_mig_7_ddr3`, 1173–1395 | ESPECIFICO_VC707 | MIG DDR3 de serie 7: pines DDR3, `sys_clk_p/n`, `ui_clk`, reset/calibración y AXI esclavo. Es el controlador DDR del VC707 y no se puede usar en Zynq UltraScale+. |
| Rama DDR4/PCIe VCU118, 1396–1910 | ESPECIFICO_VC707 (otra placa) | IP DDR4 y PCIe de VCU118; no participa en VC707 ni en KR260. |

## `ariane_peripherals_xilinx.sv`

Este módulo es un concentrador de periféricos AXI. El PLIC siempre se elabora;
UART, SPI, Ethernet, GPIO y timer usan parámetros `Incl*` (las ramas apagadas
fijan respuestas AXI inactivas). En detalle:

* **UART:** `axi2apb_64_32` + `apb_uart`, con puertos `rx_i`/`tx_o`. Es
  genérico en RTL, pero los pines del VC707 están en `vc707.xdc`.
* **SPI/SD:** `xlnx_axi_quad_spi` conectado a `spi_clk_o`, `spi_mosi`,
  `spi_miso`, `spi_ss`; el XCI y los pines SD son de la plataforma previa.
* **GPIO:** `xlnx_axi_gpio` expone LEDs y switches. No es necesario para
  arrancar CVA6 y los pines VC707 no son transferibles.
* **Ethernet:** `framing_top`/RGMII y clocking Ethernet se elaboran sólo con
  `InclEthernet`. VC707 lo deja en cero, pero los puertos, fuentes y
  constraints RGMII continúan presentes en el wrapper viejo.
* **PLIC y timer APB:** reciben IRQ de UART/SPI/Ethernet/GPIO/timer. Pueden
  quedar fuera de la primera integración mínima si no se expone ninguno de
  esos dispositivos.

## Scripts, constraints y Makefiles actuales

* El `Makefile` raíz escoge `vc707` con
  `xc7vx485tffg1761-2`, board part `xilinx.com:vc707:part0:1.4` y 20 ns.
  El target `fpga` genera `scripts/add_sources.tcl` y llama al Makefile de
  `corev_apu/fpga`.
* `corev_apu/fpga/scripts/prologue.tcl` crea siempre `ariane.xpr`, aplica el
  board part y fija `general.maxThreads 1`.
* `setup_project_only.tcl` y `run.tcl` enumeran explícitamente MIG 7 DDR3,
  clock converter, width converters, GPIO, QSPI y clock generator. `run.tcl`
  también lanza implementación y bitstream: no es apto para el objetivo de
  esta etapa.
* `vc707.xdc` asigna todos los pines VC707: reset, JTAG, UART, LEDs,
  switches, fan, RGMII y SD; contiene clocks/asynchrony propios de Ethernet.
  `ariane.xdc` agrega constraints JTAG comunes, incluidos `set_false_path`.
  Ninguno debe aplicarse a KR260.

## Decisión de estructura

Se creará `corev_apu/fpga/src/ariane_kr260.sv` como wrapper separado. Así
`ariane_xilinx.sv` y el flujo VC707 quedan intactos y comparables. El nuevo
wrapper contendrá solamente CVA6, ROM, CLINT, reset limpio, crossbar AXI
mínimo y una frontera AXI explícita hacia la futura memoria KR260. No usará
MIG 7 DDR3, IP de serie 7, MMCM del VC707, Ethernet, SPI/SD, GPIO, LEDs,
switches, fan ni constraints de sus pines.

La primera síntesis tendrá entradas lógicas `clk_i` y `rst_ni`, sin inventar
`PACKAGE_PIN`. `kr260.xdc` sólo definirá `clk_i` como clock de 40 ns. La fuente
física posterior puede ser un clock PL proveniente de PS, un Clocking Wizard o
una interfaz de placa documentada; elegirla requiere la arquitectura PS/PL.
