# Material local para trabajar con Gonza el 30 de octubre de 2026

Los archivos de placa se conservan en esta computadora. La transferencia SSH copia el respaldo y no mueve ni borra los originales.

## Estado de las dos frecuencias

| Frecuencia | Archivos y estado |
|---|---|
| 25 MHz | [Paquete conocido bueno](/home/nachofalchi/data/fpga-work/cva6-equipo/corev_apu/fpga/software/kr260_ps_boot/known_good_2026-09-18/README.md): BIT/LTX, FSBL parcheado, aplicación ARM y scripts JTAG. Tiene PASS DDR e ILA documentados. |
| 90,908 MHz | [Paquete que cerró timing](/home/nachofalchi/data/fpga-work/cva6-equipo/corev_apu/fpga/software/kr260_ps_boot/timing_closed_91mhz_2026-10-22/README.md): BIT/LTX/XSA/DCP íntegros. FSBL91 compilado con PASS de software y scripts JTAG/captura preparados; aún no se validó en placa. |

El BIT correcto para 90,9 MHz es [kr260_top.bit del paquete cerrado](/home/nachofalchi/data/fpga-work/cva6-equipo/corev_apu/fpga/software/kr260_ps_boot/timing_closed_91mhz_2026-10-22/kr260_top.bit). El resultado de `impl_1` no es el resultado cerrado.

## Repetir el conocido bueno de 25 MHz

Con la placa conectada, cuando decidan ejecutar con Gonza:

```bash
CVA6_BOOT_DIR=/home/nachofalchi/data/fpga-work/cva6-equipo/corev_apu/fpga/software/kr260_ps_boot
CVA6_XSDB_BIN=/home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vitis/bin/xsdb
"$CVA6_XSDB_BIN" "$CVA6_BOOT_DIR/known_good_2026-09-18/kr260_jtag_boot.xsdb"
"$CVA6_XSDB_BIN" "$CVA6_BOOT_DIR/known_good_2026-09-18/kr260_jtag_run.xsdb"
```

Estos comandos reinician la PS y programan la FPGA. Los scripts apuntan explícitamente al BIT/FSBL/app del paquete de 25 MHz. No se ejecutaron durante esta preparación. El PASS esperado es `STATUS0 = 0x800004000: 00000001`.

Para capturas nuevas de ILA, usar una copia del Tcl con una ruta de salida nueva; conservar la captura histórica del paquete conocido bueno. Usar siempre el LTX correspondiente al BIT programado.

## Preparar la prueba de 90,9 MHz

El FSBL91 ya se generó y compiló en `operacion/cva6_ops/fsbl91/build_20261029_1831`, fuera de los paquetes congelados. El [manifiesto de compilación](/home/nachofalchi/data/fpga-work/operacion/cva6_ops/fsbl91/build_20261029_1831/fsbl91_manifest.json) registra **PASS de software**, XSA91, IOPLL/11 y el parche que mantiene el CVA6 en reset. El [ELF91 preparado](/home/nachofalchi/data/fpga-work/operacion/cva6_ops/fsbl91/build_20261029_1831/kr260_fsbl_91mhz_patched.elf) tiene SHA256 `4b2c98d7ea93099d62b7538ce4d92b071d3672ef157b48acf7bf688df380ab87`. Esto no acredita funcionamiento en placa.

1. Revisar la [guía de automatización](guia_automatizacion.md), los hashes del plan y la conexión con la placa. Los scripts de arranque y captura para 25/91 MHz están preparados; todavía falta ejecutarlos en hardware.
2. Repetir primero la demo conocida de 25 MHz y después probar el BIT cerrado de 90,9 MHz con el FSBL91 preparado.
3. Guardar PASS/FAIL y capturas nuevas con la identidad de BIT/LTX/FSBL/XSA. La aplicación ARM de esta prueba escribe en DDR; no es un cargador genérico de programas.

El XSA y el FSBL nuevos de 90,9 MHz configuran IOPLL/11. Los FSBL históricos de 25 MHz configuran IOPLL/40 y deben conservarse para esa frecuencia. La reproducción del FSBL91 es opcional, mediante la automatización y una salida nueva; la plantilla HSI histórica de `retest_2026-10-07` apunta al XSA de 25 MHz y no debe ejecutarse tal cual para 91 MHz.

La posible restauración de la ROM original y la carga de programas en DDR se describen en el [plan de BootROM y programas DDR](/home/nachofalchi/data/fpga-work/cva6-equipo/docs/seguimiento_fpga/plan_bootrom_original_y_programas_ddr.md). Es un plan separado; no se modificó la BootROM ni el CPU.

## Herramientas que permanecen instaladas

Vivado/XSDB/HSI están en `Xilinx/2026.1`. El compilador ARM está extraído en `build/toolchain/arm-gnu-toolchain-13.3.rel1-x86_64-aarch64-none-elf` dentro de `kr260_ps_boot`; GCC, LD, AS, objcopy, cc1 y librerías se verificaron presentes. Sólo se eliminó el archivo de instalación comprimido redundante.

El [informe de verificación local](/home/nachofalchi/data/fpga-work/timing-audit/ssh_backup_20261029/archivos_placa_local_verificados.json) registra las rutas y hashes revisados. El paquete de 90,9 MHz verifica 29/29 archivos. Los 17 archivos de contenido del paquete de 25 MHz verifican; su manifiesto histórico tiene una autoentrada incorrecta, ya documentada, que no implica corrupción del BIT/FSBL.

## Antes de salir

Llevar notebook y cargador, KR260, fuente de la placa y cable USB de datos para JTAG. Los paquetes de 25 y 90,9 MHz, los scripts y las herramientas están locales. La existencia de archivos y sus hashes se revisaron; la conexión física, USB y servidor JTAG se comprueban al conectar la placa.

Para la demo conocida, los resultados se leen por JTAG; no se debe depender de una consola UART. Si se arma una captura ILA nueva, armar el analizador antes de lanzar la aplicación y guardar la salida en un archivo nuevo.
