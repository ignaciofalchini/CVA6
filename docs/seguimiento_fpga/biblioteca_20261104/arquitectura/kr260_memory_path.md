# Camino de memoria CVA6 y frontera KR260

## Camino actual en VC707

La configuración sigue siendo `TARGET_CFG=cv64a6_imafdc_sv39`, `XLEN=64`.
No se modificará ningún archivo del core para este port.

Para una instrucción como `load x1, 0(x2)`, el recorrido relevante es:

```text
CVA6 LSU
  -> subsistema de cachés configurado por cv64a6_imafdc_sv39
  -> puerto NOC AXI de cva6
  -> corev_apu/src/ariane.sv (noc_req_o / noc_resp_i)
  -> ariane_xilinx.sv: slave[0]
  -> axi_xbar_intf
  -> master[ariane_soc::DRAM], por rango 0x8000_0000..0xBFFF_FFFF
  -> axi_riscv_atomics_wrap
  -> AXI64 `dram`
  -> xlnx_axi_clock_converter (clock CVA6 -> UI clock MIG)
  -> AXI `s_axi_*`
  -> xlnx_mig_7_ddr3
  -> DDR3 física del VC707
```

El crossbar también enruta ROM (`0x0001_0000`) a `axi2mem` + `bootrom_64`,
CLINT a `clint`, y las demás ventanas a debug/periféricos. Esto significa que
el primer fetch no requiere DDR: CVA6 arranca desde la bootrom integrada. La
bootrom actual sí contiene software orientado a UART/SPI/SD, por lo que su
ejecución completa necesitará adaptar o sustituir el firmware cuando se
definan los periféricos reales de KR260; conservarla ahora preserva el vector
de reset y el mecanismo de arranque.

## Interfaz que sale del core

`ariane.sv` es un wrapper fino de `cva6`. Expone `noc_req_o` y consume
`noc_resp_i`, de tipos `ariane_axi::req_t`/`ariane_axi::resp_t`. El sistema
FPGA los adapta a un `AXI_BUS` de 64 bits de dirección/datos. En el VC707 los
dos iniciadores del crossbar son CVA6 y el System Bus Access del Debug Module;
por ello los IDs del lado de destinos tienen 5 bits (4 bits del master más
`$clog2(2)`).

`axi_riscv_atomics_wrap` está después del crossbar y antes de memoria. Se
conserva porque convierte/serializa las operaciones atómicas RISC-V para una
memoria AXI convencional; retirarlo cambiaría la semántica observada por la
memoria y no es una limpieza segura.

## Frontera propuesta para KR260

La primera integración KR260 termina en una interfaz AXI4 de PL explícita:

```text
CVA6 -> caches -> NOC AXI -> crossbar mínimo -> axi_riscv_atomics_wrap
     -> m_axi_mem_* (AXI4, 64-bit data/address, 5-bit ID) -> [pendiente KR260]
```

La frontera `m_axi_mem_*` conserva los cinco canales AXI (`AW`, `W`, `B`,
`AR`, `R`), incluidos `ATOP`, `CACHE`, `PROT`, `QOS`, `REGION` y `USER` donde
el bus interno los transporta. Es una salida del top KR260, no un stub de
memoria ni una respuesta falsa. Por esa razón una síntesis exitosa sólo prueba
que la integración PL es consistente: no prueba que las cargas/almacenamientos
lleguen aún a DDR.

## Pendiente arquitectónico explícito

La DDR de KR260 pertenece al subsistema Zynq UltraScale+ MPSoC/PS, no al MIG
DDR3 de serie 7. Conectar `m_axi_mem_*` exige escoger y diseñar una ruta real,
por ejemplo un PS configurado con un puerto HP/HPC/NoC adecuado, o una
arquitectura PL soportada por el hardware y su clock/reset asociados. También
habrá que decidir:

1. mapa físico y tamaño para mantener o ajustar la ventana CVA6
   `0x8000_0000`;
2. dominios de clock y reset, incluyendo conversores AXI sólo si los clocks
   reales difieren;
3. adaptación de ancho/ID/ATOP requerida por el puerto de PS elegido;
4. reset y disponibilidad de memoria antes de liberar CVA6;
5. firmware bootrom y consola/periféricos de la plataforma real.

No se implementa ninguno de esos puntos a ciegas ni se presenta una memoria
falsa como solución. El wrapper mínimo mantiene visible el punto exacto de
integración para resolverlos en la siguiente etapa.
