# KR260: ILA y VIO para depurar memoria

## Alcance

`ariane_kr260_debug.sv` envuelve al top mínimo `ariane_kr260` sin modificarlo. La variante mínima sigue siendo independiente de los IP de debug. El wrapper usa dos IP reales del catálogo de Vivado 2026.1, creados por `create_kr260_debug_ips.tcl`:

- `kr260_axi_ila`: ILA de 9 probes, 2048 muestras y clock `clk_i`.
- `kr260_reset_vio`: VIO con una entrada de 2 bits y una salida de 1 bit.

La profundidad 2048 permite ver varios bursts y su respuesta sin el costo desmedido de una captura muy larga. La síntesis atribuye al ILA 17 RAMB36, 1587 LUT y 2667 FF; el VIO usa 103 LUT y 250 FF.

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

Un handshake ocurre solamente en un ciclo con `VALID && READY`.

### Lectura esperada

1. `probe1[12]` sube con la dirección en `probe0`.
2. Cuando también sube `probe1[11]`, la dirección fue aceptada.
3. Cada ciclo con `probe3[4] && probe3[3]` transfiere un beat en `probe2`.
4. `probe3[0]` identifica el último beat y `probe3[2:1]` debe ser normalmente `00`.

Para la prueba de bootrom conviene disparar por `probe1[12] && probe1[11]` y `probe0 == 64'h0000_0000_8000_0000`.

### Escritura esperada

1. `probe5[12]` presenta la dirección en `probe4`; `probe5[11]` completa el handshake AW.
2. `probe7[2]` presenta el patrón en `probe6`; `probe7[1]` completa cada handshake W.
3. `probe7[10:3]` indica qué bytes cambian y `probe7[0]` marca el beat final.
4. El destino termina con `probe8[1]`; la transacción finaliza cuando también está alto `probe8[0]`. `probe8[3:2]` debe ser normalmente `00`.

AXI permite desacoplar AW y W: no es obligatorio que ambos handshakes ocurran en el mismo ciclo.

## VIO y soft reset

`probe_in0[1]` observa el reset externo activo-bajo `rst_ni`; `probe_in0[0]` observa el reset efectivo `core_rst_ni`. `probe_out0[0]` controla `soft_reset` y se inicializa a cero.

La combinación es:

```systemverilog
assign core_rst_ni = rst_ni & ~soft_reset;
```

Por lo tanto, el VIO sólo puede agregar una aserción de reset. No sustituye ni puede anular el reset físico. Esta lógica existe exclusivamente en el wrapper debug.

## Generación y síntesis reproducibles

Desde `corev_apu/fpga`:

```bash
make BOARD=kr260 \
  XILINX_PART=xck26-sfvc784-2LV-c \
  XILINX_BOARD=xilinx.com:kr260_som:part0:2.0 \
  VIVADO=/ruta/a/Vivado/2026.1/bin/vivado \
  kr260-debug-synth
```

El target crea los IP bajo `corev_apu/fpga/ip/kr260_debug`, genera sus productos, ejecuta sus síntesis OOC secuencialmente y después elabora y sintetiza `ariane_kr260_debug` con `general.maxThreads=1` y un solo job. No contiene comandos de implementación ni de bitstream. Los `.xci`, DCP y netlists son productos regenerables y no son fuente versionada; el Tcl es la fuente de verdad.

Resultado comprobado con Vivado 2026.1:

- elaboración RTL: 0 errores, 0 critical warnings;
- síntesis del top: `synth_design Complete!`, 0 errores y 0 critical warnings durante síntesis;
- ILA y VIO reconocidos como cores Chipscope, con todos los anchos esperados;
- recursos totales: 59.245 LUT, 31.794 FF, 55 RAMB36 y 27 DSP;
- black boxes esperadas al abrir el DCP: `dbg_hub` y tres módulos `unread` intencionales sin salida; ninguna black box de IP de usuario inesperada.

El timing de síntesis no sustituye timing post-place-and-route. El reporte muestra setup holgado a 25 MHz, pero violaciones hold estimadas antes de implementación; por regla de esta tanda no se ejecutó implementación.

## Dónde aparecen en Vivado

Al abrir `ariane_kr260_debug/ariane_kr260_debug.xpr`:

1. En **Sources → IP Sources** aparecen `kr260_axi_ila` y `kr260_reset_vio`.
2. En **Synthesis → Open Synthesized Design**, `get_debug_cores` devuelve ambos cores.
3. En hardware, después de que exista un bitstream de una etapa futura, **Hardware Manager** mostrará el ILA y VIO bajo el dispositivo programado. Esta tanda no generó bitstream y, por lo tanto, todavía no demuestra captura en la placa.

