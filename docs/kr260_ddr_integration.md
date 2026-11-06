# KR260: integración DDR previa a síntesis

La top es `kr260_top`. El proyecto conserva el nombre `ariane_kr260_debug`.
El núcleo, crossbar, CLINT, debug RISC-V y atomics siguen en `ariane_kr260`.

## Mapa reservado para CVA6

| Vista | Base | Último byte | Tamaño |
|---|---|---|---|
| CVA6 | `0x80000000` | `0xbfffffff` | 1 GiB |
| PS (DDR alta) | `0x800000000` | `0x83fffffff` | 1 GiB |

`kr260_addr_pkg::ps_ddr_address` traduce AWADDR y ARADDR después de atomics.
La fórmula conserva el desplazamiento dentro de la ventana. El crossbar sigue
limitando el destino DRAM a su ventana de 1 GiB. La constante de fin es exclusiva.
No se habilitan los 4 GiB completos para CVA6 en esta etapa.

**La reserva es un contrato pendiente de aplicar al software del PS.** Ningún
ELF, heap, stack, DMA o cargador del PS debe ocupar ese GiB. Los segmentos del BD
no reservan memoria, ni generan esta traducción por sí mismos.

## AXI y reloj

El BD expone HP0 de 64 bits, direcciones de 49 bits e IDs de 6 bits. La top
extiende los IDs de solicitud de 5 bits con cero y recupera los 5 bits originales
en las respuestas. Las aserciones de simulación comprueban el bit superior,
la ventana CVA6 y que los ATOP ya fueron consumidos antes del PS.
QOS, CACHE y PROT se propagan; AWUSER/ARUSER del PS se fijan en cero. Las
respuestas USER no existen en HP0 y el sistema recibe cero. REGION y WUSER no
se transmiten. El bloque existente consume AMO/LRSC y elimina los LOCK hacia
memoria; no ofrece exclusión frente a maestros del PS que eludan ese bloque.

`pl_clk0` alimenta CVA6, ILA y VIO; dentro del BD también alimenta HP0.
El puerto PL externo `clk_i` y sus restricciones de pin C3 fueron retirados.
El XDC generado por el PS define `clk_pl_0` con período 40 ns; la propiedad del
BD informa 24.999.750 Hz. Se conserva el XDC del fabricante, sin editarlo ni
crear un segundo reloj para la misma fuente. El timing final queda pendiente.

## Reset y arranque: condición previa al uso en hardware

`rst_ni = ps_reset_n & ~soft_reset`; se conserva `rstgen`.
El script de preparación configura el valor inicial del VIO en cero para
permitir arranque automático. **Eso requiere que el flujo del PS mantenga
`pl_resetn0` activo hasta que DDR, reloj e interfaz estén inicializados.**
La señal no significa automáticamente DDR lista. No se debe programar y soltar
el sistema sobre un PS de estado desconocido.

La secuencia de FSBL/aplicación sin OS, reserva en linker/cargador y liberación
de reset deben completarse y verificarse con el XSA/bitstream definitivos.
No se ha creado ni validado BOOT.BIN en esta etapa previa a síntesis.
El VIO reinicia el sistema CVA6, no la DDR del PS. Usarlo sólo con AXI inactivo,
por ejemplo después de la terminación de la prueba; no hay drenaje de
transacciones automático para un reset arbitrario durante tráfico.

## BootROM de prueba

`KR260_MEMORY_TEST_BOOTROM` configura cero regiones cacheables en la variante
KR260: las lecturas de comprobación deben llegar a memoria. La arquitectura de
caché no se elimina, y la configuración global de CVA6 no se modifica.

La ROM escribe y compara 16 KiB con dos patrones complementarios dependientes
de la dirección; luego escribe TODOS los puntos dispersos antes de leerlos:
base, potencias de dos desde 8 KiB hasta 512 MiB, y último doubleword del GiB.
Esto detecta el antiguo aliasing de 8 KiB y varios errores de direccionamiento.
No es una prueba exhaustiva del GiB ni de AMO/LRSC.

El estado se publica en CVA6 `0x80004000` / PS `0x800004000`:

| Desplazamiento | Significado |
|---|---|
| +0 | 1 PASS; todos unos FAIL |
| +8 | dirección CVA6 del primer fallo |
| +16 | dato esperado |
| +24 | dato leído |

El punto de estado también participa en la prueba dispersa: leerlo sólo al
terminar, confirmado por el PC estacionario en ILA. `test_pass` y `fail_halt`
están identificados en el desensamblado generado. Una excepción de acceso o
bloqueo AXI no se convierte automáticamente en FAIL: observar PC y respuestas
AXI y aplicar timeout desde el procedimiento de prueba.

## Preparación y verificación

Guardar y cerrar la GUI antes de usar el script batch sobre el mismo proyecto.

```
make -C corev_apu/fpga/src/bootrom/kr260_memory_test all
python3 corev_apu/fpga/tests/check_ddr_bootrom.py
vivado -mode batch -source corev_apu/fpga/scripts/check_kr260_ddr_rtl.tcl
```

El primer comando requiere `riscv64-unknown-elf-*` en PATH o especificar
`RISCV_TOOLCHAIN_BIN`. El script Tcl actualiza las fuentes con el wrapper
Verilog de puertos planos, retira del proyecto el BD/wrapper BRAM sin borrar
los archivos, regenera productos, desactiva el checkpoint incremental anterior
y elabora RTL con `synth_design -rtl`. **No lanza síntesis de lógica, runs de
síntesis, implementación ni bitstream.**

`tests/kr260_address_tb.sv` comprueba en Verilator los límites de traducción y
los 30 bits del desplazamiento. `check_ddr_bootrom.py` ejecuta el binario real
en un modelo mínimo de instrucciones RV64 y comprueba PASS, corrupción y alias
de 8 KiB, además de comparar el binario con la ROM RTL. No simula CVA6 ni AXI.

Los reportes de Vivado se guardan en `reports/kr260_ddr_pre_synth/`.
La validación en placa, timing post-route, coherencia con software ARM y arranque
frío siguen siendo trabajo posterior a esta etapa.
