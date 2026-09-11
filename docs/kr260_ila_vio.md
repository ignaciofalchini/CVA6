# KR260: ILA y VIO para depurar memoria

## Alcance

`ariane_kr260_debug.sv` envuelve al top mínimo `ariane_kr260` sin modificarlo. La variante mínima sigue siendo independiente de los IP de debug. El wrapper usa dos IP reales del catálogo de Vivado 2026.1, creados por `create_kr260_debug_ips.tcl`:

- `kr260_axi_ila`: ILA de 21 probes (`probe0` a `probe20`), 2048 muestras y clock `clk_i`.
- `kr260_reset_vio`: VIO con una entrada de 2 bits y una salida de 1 bit.

El wrapper expone solamente `clk_i`. El JTAG DTM propio de CVA6 queda mantenido en reset; esto no afecta el acceso a ILA/VIO, que usa la cadena JTAG de configuración de la FPGA. `constraints/kr260.xdc` asigna `clk_i` a C3, LVCMOS18, con período de 40 ns (25 MHz).

La profundidad 2048 permite ver varios bursts y su respuesta. Los recursos de la configuración de 21 probes deben medirse después de regenerar y sintetizar el IP; las cifras históricas no describen esta versión.

## Mapa de probes del ILA

| Probe | Ancho | Señal o agrupación | Significado |
|---|---:|---|---|
| `probe0` | 64 | `m_axi_mem_araddr` | Dirección de lectura. |
| `probe1[12]` | 1 | `m_axi_mem_arvalid` | El master ofrece una solicitud AR válida. |
| `probe1[11]` | 1 | `m_axi_mem_arready` | El destino acepta la solicitud AR. |
| `probe1[10:3]` | 8 | `m_axi_mem_arlen` | Beats menos uno del burst de lectura. |
| `probe1[2:0]` | 3 | `m_axi_mem_arsize` | Log2 de bytes por beat; `3` representa 8 bytes. |
| `probe2` | 64 | `m_axi_mem_rdata` | Datos devueltos por memoria. |
| `probe3[4]` | 1 | `m_axi_mem_rvalid` | El destino presenta un beat R válido. |
| `probe3[3]` | 1 | `m_axi_mem_rready` | CVA6 acepta el beat R. |
| `probe3[2:1]` | 2 | `m_axi_mem_rresp` | Respuesta AXI: `00` OKAY, `01` EXOKAY, `10` SLVERR, `11` DECERR. |
| `probe3[0]` | 1 | `m_axi_mem_rlast` | Último beat del burst R. |
| `probe4` | 64 | `m_axi_mem_awaddr` | Dirección de escritura. |
| `probe5[12]` | 1 | `m_axi_mem_awvalid` | El master ofrece una solicitud AW válida. |
| `probe5[11]` | 1 | `m_axi_mem_awready` | El destino acepta la solicitud AW. |
| `probe5[10:3]` | 8 | `m_axi_mem_awlen` | Beats menos uno del burst de escritura. |
| `probe5[2:0]` | 3 | `m_axi_mem_awsize` | Log2 de bytes por beat. |
| `probe6` | 64 | `m_axi_mem_wdata` | Datos escritos. |
| `probe7[10:3]` | 8 | `m_axi_mem_wstrb` | Byte lanes válidos de `wdata`; `ff` significa los 8 bytes. |
| `probe7[2]` | 1 | `m_axi_mem_wvalid` | El master presenta un beat W válido. |
| `probe7[1]` | 1 | `m_axi_mem_wready` | El destino acepta el beat W. |
| `probe7[0]` | 1 | `m_axi_mem_wlast` | Último beat del burst W. |
| `probe8[3:2]` | 2 | `m_axi_mem_bresp` | Respuesta final de escritura AXI. |
| `probe8[1]` | 1 | `m_axi_mem_bvalid` | El destino presenta la respuesta B. |
| `probe8[0]` | 1 | `m_axi_mem_bready` | CVA6 acepta la respuesta B. |
| `probe9` | 1 | `mem_rst_n` | Reset sincronizado compartido por CVA6, crossbar, atomics y controlador BRAM: 0 = reset, 1 = liberado. |
| `probe10` | 32 | `m_debug_instruction` | Instrucción del frontend, no necesariamente la del PC de commit. |
| `probe11` | 1 | `m_debug_instruction_valid` | Validez de la entrada de fetch observada. |
| `probe12` | 64 | `m_debug_commit_pc` | PC del puerto de commit 0. |
| `probe13` | 1 | `m_debug_commit_valid` | Validez en commit 0. |
| `probe14` | 1 | `m_debug_commit_ack` | Acuse de commit 0; interpretar junto con validez y excepciones. |
| `probe15` | 64 | `m_debug_mem_paddr` | Dirección física de memoria observada internamente. |
| `probe16` | 64 | `m_debug_lsu_vaddr` | Dirección virtual de la LSU. |
| `probe17` | 8 | `m_debug_lsu_be` | Byte enables de la LSU. |
| `probe18` | 8 | `m_debug_commit_op` | Código interno de operación en commit 0. |
| `probe19` | 4 | `m_debug_lsu_fu` | Código interno de unidad funcional de la LSU. |
| `probe20[19:15]` | 5 | `m_axi_mem_awid` | ID de la solicitud de escritura. |
| `probe20[14:10]` | 5 | `m_axi_mem_bid` | ID de la respuesta de escritura. |
| `probe20[9:5]` | 5 | `m_axi_mem_arid` | ID de la solicitud de lectura. |
| `probe20[4:0]` | 5 | `m_axi_mem_rid` | ID de cada beat de respuesta de lectura. |

Un handshake ocurre solamente en un ciclo con `VALID && READY`. Comparar el ID de cada respuesta con el de su solicitud aceptada, no necesariamente con el ID de solicitud presente en ese mismo ciclo. Un ID con VALID=0 no representa una transacción válida.

El ILA observa el puerto externo hacia BRAM, no los accesos a la bootROM. Frontend, commit y LSU son etapas distintas; las direcciones pueden conservar valores anteriores cuando no hay operación válida. Solo se observa commit 0 y no se capturan excepciones.

### Lectura esperada

1. `probe1[12]` sube con la dirección en `probe0`.
2. Cuando también sube `probe1[11]`, la dirección fue aceptada.
3. Cada ciclo con `probe3[4] && probe3[3]` transfiere un beat en `probe2`.
4. `probe3[0]` identifica el último beat y `probe3[2:1]` debe ser normalmente `00`.

Un trigger AR sirve para un programa que lea BRAM. La bootROM actual solo genera escrituras: usar el trigger AW descrito a continuación.

### Escritura esperada

1. `probe5[12]` presenta la dirección en `probe4`; `probe5[11]` completa el handshake AW.
2. `probe7[2]` presenta el patrón en `probe6`; `probe7[1]` completa cada handshake W.
3. `probe7[10:3]` indica qué bytes cambian y `probe7[0]` marca el beat final.
4. El destino termina con `probe8[1]`; la transacción finaliza cuando también está alto `probe8[0]`. `probe8[3:2]` debe ser normalmente `00`.

AXI permite desacoplar AW y W: no es obligatorio que ambos handshakes ocurran en el mismo ciclo.

Para la primera escritura, disparar con `probe5[12] && probe5[11]` y `probe4 == 64'h0000_0000_8000_0000`. Registrar AWID en ese handshake y comprobar que la respuesta B correspondiente devuelve el mismo BID. Para lecturas, registrar ARID y compararlo con RID de cada beat de su respuesta, hasta RLAST.

## VIO y soft reset

`probe_in0[1]` observa `soft_reset`; `probe_in0[0]` observa `mem_rst_n`. `probe_out0[0]` controla `soft_reset` y se inicializa a uno para mantener el sistema en reset después de programar la FPGA. No cambian los anchos ni la configuración del IP VIO.

`ariane_kr260` recibe `~soft_reset`, lo combina con `~ndmreset` y sincroniza la liberación mediante `rstgen`. Su salida `mem_rst_no` llega a `mem_rst_n` en el wrapper. Al bajar `soft_reset`, `mem_rst_n` sube después de cuatro flancos de reloj con la configuración actual. El ILA y el VIO conservan su reloj durante el reset.

### Aplicar la configuración de 21 probes

Con el proyecto debug abierto y sin runs en ejecución, ejecutar en su consola Tcl:

```tcl
source /home/nachofalchi/data/fpga-work/cva6-equipo/corev_apu/fpga/scripts/create_kr260_debug_ips.tcl
get_property CONFIG.C_NUM_OF_PROBES [get_ips kr260_axi_ila]
get_property CONFIG.C_PROBE20_WIDTH [get_ips kr260_axi_ila]
```

Los valores esperados son `21` y `20`. El script regenera los IP y ejecuta sus síntesis OOC, no la síntesis del top ni la implementación. Hasta completarlo, el RTL con `probe20` no coincide con el IP antiguo de 20 probes. Después actualizar el orden de compilación, comprobar la elaboración y ejecutar una nueva síntesis e implementación. Usar el BIT y LTX de esa misma generación.

Para capturar el inicio, mantener `soft_reset=1`, armar el ILA y recién entonces cambiar `soft_reset` a 0. El reset debe liberarse (`probe9=1`) antes de la actividad AXI.

## Síntesis del proyecto guardado en Vivado

Guardar y cerrar primero el proyecto en la GUI. Desde `corev_apu/fpga`:

```bash
make BOARD=kr260 \
  XILINX_PART=xck26-sfvc784-2LV-c \
  XILINX_BOARD=xilinx.com:kr260_som:part0:2.0 \
  VIVADO=/ruta/a/Vivado/2026.1/bin/vivado \
  kr260-debug-synth
```

El target abre el proyecto existente `ariane_kr260_debug/ariane_kr260_debug.xpr` y utiliza su BD `ariane_kr260_debug/ariane_kr260_debug.srcs/sources_1/bd/ariane_kr260_ps_bd/ariane_kr260_ps_bd.bd`. Las rutas se resuelven desde el script, no desde el directorio de trabajo. Conserva las fuentes, la selección de bootrom, la configuración de los IP, las constraints y las estrategias guardadas en el proyecto: ya no lo recrea con `create_project -force` ni reconfigura el ILA/VIO desde otro Tcl.

Valida el BD, genera sus productos y wrapper, y después elabora y lanza la síntesis de `ariane_kr260_debug` con `general.maxThreads=1` y un solo job. No contiene comandos de implementación ni de bitstream, ni resetea automáticamente los runs existentes. Si Vivado requiere reiniciar una síntesis anterior, hacerlo explícitamente desde la GUI antes de guardar y cerrar.

El proyecto guardado y su BD son ahora necesarios para este target: si faltan, el script se detiene, sin recurrir a una copia antigua. La copia que antes estaba en `src/` quedó archivada junto con su layout en `corev_apu/fpga/backups/kr260_bd_antes_ids_y_reset_2026-09-10/`; no se utiliza ni se sincroniza automáticamente.

Resultado histórico comprobado con Vivado 2026.1, anterior a este cambio de flujo (no constituye validación de una nueva síntesis):

- elaboración RTL: 0 errores, 0 critical warnings;
- síntesis del top: `synth_design Complete!`, 0 errores y 0 critical warnings durante síntesis;
- ILA y VIO reconocidos como cores Chipscope, con todos los anchos esperados;
- recursos totales: 59.245 LUT, 31.794 FF, 55 RAMB36 y 27 DSP;
- black box esperada al abrir el DCP: `dbg_hub`; ninguna black box de IP de usuario inesperada.

El timing de síntesis no sustituye timing post-place-and-route. El reporte muestra setup holgado a 25 MHz, pero violaciones hold estimadas antes de implementación; por regla de esta tanda no se ejecutó implementación.

## Dónde aparecen en Vivado

Al abrir `ariane_kr260_debug/ariane_kr260_debug.xpr`:

1. En **Sources → IP Sources** aparecen `kr260_axi_ila` y `kr260_reset_vio`.
2. En **Synthesis → Open Synthesized Design**, `get_debug_cores` devuelve ambos cores.
3. En **Hardware Manager** aparecen el ILA y VIO bajo el dispositivo programado. El 11/09/2026 se verificó en una captura un tramo de 54 escrituras consecutivas con datos correctos y AWID=BID=1. Esta comprobación no cubre lectura de RAM ni todas las funciones del procesador; persisten errores intermitentes al descargar capturas.

El XPR, BD, XCI y las imágenes RTL de las ROM se conservan en Git, mientras que los productos de síntesis e implementación quedan en el backup. Ver [versionado y recuperación](kr260_versionado_y_recuperacion.md) para el alcance y las precauciones al abrir una copia sin productos generados.
