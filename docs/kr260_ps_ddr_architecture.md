# KR260 PS DDR architecture for CVA6

## Decision

Use the Zynq UltraScale+ MPSoC processing-system slave port
`S_AXI_HP0_FPD`, configured as AXI4, 64-bit data, and clocked with the same
PS-generated PL clock as CVA6. HP0 is the simplest correct path because this
design does not require cache coherency with the Arm APU.

The existing CVA6 memory range and the PS physical DDR aperture do not have the
same base. The integration therefore performs an explicit translation:

```text
CVA6 0x0000_0000_8000_0000 .. 0x0000_0000_bfff_ffff
  -   0x0000_0000_8000_0000
PS   0x0000_0000_0000_0000 .. 0x0000_0000_3fff_ffff
```

This exposes the lower 1 GiB of PS DDR to the existing 1 GiB CVA6 DRAM window.
It is not address-bit truncation: the subtraction and accepted source range are
visible in `ariane_kr260_system.sv` and guarded by simulation assertions.

## Recommended architecture

```text
                           Programmable Logic (PL)
  +--------------------------------------------------------------------+
  | CVA6 RV64 (`cv64a6_imafdc_sv39`)                                   |
  |   |                                                                |
  |   v                                                                |
  | I/D caches + MMU + FPU                                             |
  |   |                                                                |
  |   v                                                                |
  | AXI crossbar                                                       |
  |   |                                                                |
  |   v                                                                |
  | `axi_riscv_atomics_wrap`                                           |
  |   |  AXI4+ATOP, addr64/data64/id5/user64                           |
  |   v                                                                |
  | `m_axi_mem_*`                                                      |
  |   |                                                                |
  |   v                                                                |
  | explicit boundary adapter (`ariane_kr260_system.sv`)               |
  |   - address: subtract 0x8000_0000, then require result < 1 GiB      |
  |   - ID: zero-extend 5 -> 6; response bit 5 must remain zero         |
  |   - USER: discard inactive CVA6 USER, drive PS AW/ARUSER = 0        |
  |   - ATOP: require zero after the atomics adapter                    |
  |   - data/protocol/clock: unchanged                                 |
  |   |                                                                |
  +---|----------------------------------------------------------------+
      v                         Processing System (PS)
  `S_AXI_HP0_FPD` (AXI4, addr49/data64/id6, non-coherent)
      |
      v
  PS full-power-domain interconnect
      |
      v
  PS DDR controller/PHY
      |
      v
  K26 SOM DDR4
```

The generated Block Design also provides `pl_clk0`, requested at 25 MHz and
reported by Vivado as 24.999750 MHz, and a synchronized active-low reset from
`pl_resetn0` through `proc_sys_reset`. CVA6 and HP0 use this single clock
domain, so no AXI Clock Converter is necessary.

## Evidence from the installed toolchain

The primary probe is reproducible with
`corev_apu/fpga/scripts/inspect_kr260_ps_interfaces.tcl`. It instantiated
`xilinx.com:ip:zynq_ultra_ps_e:3.5` in Vivado 2026.1 with board part
`xilinx.com:kr260_som:part0:2.0`. Vivado reported:

| Property | `S_AXI_HP0_FPD` | `S_AXI_HPC0_FPD` |
| --- | ---: | ---: |
| Protocol | AXI4 | AXI4 |
| Address width | 49 | 49 |
| Configured data width | 64 | 64 |
| ID width | 6 | 6 |
| AWUSER / ARUSER | 1 / 1 | 1 / 1 |
| BUSER / RUSER / WUSER | 0 / 0 / 0 | 0 / 0 / 0 |
| Bursts | yes, maximum 256 beats | yes, maximum 256 beats |
| Narrow bursts | supported | supported |
| LOCK | supported | supported |
| Read/write outstanding | 16 / 16 | 16 / 16 |

The installed KR260 2.0 board preset identifies DDR4, a 64-bit DDR controller
bus, DDR4-2400 settings, and a 1200 MHz DDR controller clock. Those values stay
owned by the board preset; the port does not duplicate or invent DDR pins.

The generated PS metadata gives the system address apertures:

```text
DDR_LOW  0x0000_0000 .. 0x7fff_ffff
DDR_HIGH 0x8_0000_0000 .. 0x8_7fff_ffff
```

Vivado additionally reports that `0x7ff0_0000..0x7fff_ffff` is reserved for
the PMU. The selected physical range `0x0000_0000..0x3fff_ffff` does not touch
that reservation. It still needs a system-software ownership policy before the
Arm APU and CVA6 can use DDR concurrently.

Relevant local sources of truth, in order:

1. Vivado 2026.1 IP query report:
   `reports/kr260_next_steps/memory/ps_interfaces_vivado_2026_1.txt`.
2. Installed board preset:
   `Xilinx/2026.1/data/xhub/boards/XilinxBoardStore/boards/Xilinx/kr260_som/2.0/preset.xml`.
3. Installed AMD example
   `XilinxCEDStore/ced/Xilinx/IPI/MPSoC_Ext_Platform/run.tcl`, which classifies
   HP ports as `S_AXI_HP`, HPC ports as `S_AXI_HPC`, and associates each with
   its exact `*_DDR_LOW` memory segment.
4. Official AMD references: [Zynq UltraScale+ MPSoC TRM UG1085](https://docs.amd.com/v/u/en-US/ug1085-zynq-ultrascale-trm),
   [Zynq UltraScale+ Processing System IP PG201](https://docs.amd.com/r/en-US/pg201-zynq-ultrascale-plus-processing-system),
   and [Kria KR260 product page](https://www.amd.com/en/products/system-on-modules/kria/k26/kr260-robotics-starter-kit.html).

The AMD portal was reachable from this environment, but its documentation body
is loaded dynamically. Consequently, numeric interface properties in this
document come from the installed 2026.1 IP/board metadata rather than copied
from an inaccessible web rendering.

## AXI compatibility and adaptation

### Address

CVA6 emits 64-bit addresses, but only its decoded 1 GiB DRAM range reaches this
boundary. HP0 accepts 49-bit physical addresses. The adapter first subtracts
the CVA6 base and only then takes bits `[48:0]`; assertions reject any request
outside the source window. No address-width converter is needed after this
explicit remapping.

The reason a translation is mandatory is easy to miss: the PS `DDR_LOW` range
has a size of exactly `0x8000_0000`, so CVA6 address `0x8000_0000` is the first
address outside that aperture, not its beginning.

### Data and bursts

Both sides are 64-bit AXI4 and support byte strobes, narrow transfers, and
bursts. HP0 supports up to 256 beats; CVA6 cache fills are much shorter. No Data
Width Converter or Protocol Converter is needed.

### IDs

The crossbar-facing CVA6 boundary has 5-bit IDs; HP0 has 6-bit IDs. The adapter
zero-extends requests. Because every issued ID has bit 5 clear, the returned
ID's bit 5 must also be clear and the low five bits can be returned to CVA6.
Assertions check this invariant. A SmartConnect ID adapter would be useful if
future masters were added, but is unnecessary for this one-to-one connection.

### USER and REGION

The CVA6 configuration structurally sizes USER at 64 bits but sets both
`DataUserEn=0` and `FetchUserEn=0`; the sideband carries no active function.
HP0 exposes only one AWUSER and one ARUSER bit and no W/B/R USER. The bridge
therefore drives the PS request USER bits to zero, discards CVA6 request USER
and REGION, and returns zero on CVA6 BUSER/RUSER. Assertions verify the CVA6
outputs remain zero.

### ATOP, LOCK, and exclusives

The PS AXI4 interface has no AXI5 ATOP signal. This is safe only because
`axi_riscv_atomics_wrap` remains before the boundary:

- `axi_riscv_amos` recognizes nonzero ATOP and emits ordinary reads/writes;
  its master-side `AWATOP` default is zero.
- `axi_riscv_lrsc` maintains the reservation table in PL and forces its
  master-side ARLOCK/AWLOCK to zero.

The system bridge does not silently reinterpret atomics; it asserts that ATOP
and LOCK are zero at the boundary. The PS port's LOCK pin remains connected,
but ordinary CVA6 traffic drives it low.

### Clock and reset

`pl_clk0` clocks CVA6, HP0 `saxihp0_fpd_aclk`, and `proc_sys_reset`. The PS
active-low `pl_resetn0` is explicitly inverted into the reset controller's
active-high external reset input. `peripheral_aresetn` then releases the CVA6
and interface reset synchronously. No arbitrary external clock or reset pin is
introduced.

## Alternatives considered

### `S_AXI_HP0_FPD` — selected

Advantages:

- direct PL-master access to PS DDR;
- exact 64-bit data-width match;
- full AXI4 bursts, 6-bit IDs, and ample outstanding capacity;
- non-coherent behavior matches the current CVA6/PS ownership model;
- no SmartConnect, data-width, protocol, or clock converter required.

Disadvantages:

- the APU cannot transparently snoop the private CVA6 caches;
- shared buffers require explicit software cache maintenance or uncached
  mappings on both processors;
- the CVA6 and PS address maps require the explicit offset adapter.

HP1/HP2/HP3 are equivalent options if HP0 is later needed by another PL master.
There is no current reason to consume a different port.

### `S_AXI_HPC0_FPD` / `S_AXI_HPC1_FPD`

HPC ports route through the coherent PS path/CCI and can make suitable PL
transactions coherent with the Arm APU caches. Their basic widths and burst
capacity match HP. They do not, however, make the private CVA6 cache itself a
coherent agent. Correct use also depends on coherent transaction attributes
and a concrete APU-sharing requirement. That extra semantic surface provides
no benefit for the standalone CVA6 memory smoke test, so HPC is not selected.

### `S_AXI_LPD`, ACP, and ACE

The low-power-domain slave path is intended for different power/performance
trade-offs and is not the direct high-performance DDR choice. ACP/ACE expose
stronger coherency protocols and would require a coherent master/adapter that
the current AXI4+ATOP boundary is not. They add complexity without satisfying a
current requirement.

### PS HPM ports

`M_AXI_HPM*_FPD` run in the opposite direction: they let the PS act as an AXI
master toward PL slaves. They cannot accept CVA6 memory requests.

### NoC

The K26 is a Zynq UltraScale+ MPSoC. Vivado exposes the PS AXI HP/HPC paths and
PS DDR controller; it does not expose a Versal-style programmable NoC for this
device. A NoC is therefore not an integration option here.

### SmartConnect / AXI Interconnect

Either can be inserted later for multiple initiators/targets, clock-domain
crossing, register slices, ID management, or data-width conversion. In this
one-master, one-target, one-clock, equal-width system it would obscure the
necessary address translation and consume resources without solving a present
incompatibility.

## Prototype and reproducibility

The prototype is intentionally separate from `ariane_kr260.sv`:

- `corev_apu/fpga/src/ariane_kr260_system.sv`: address/ID/USER/ATOP boundary.
- `corev_apu/fpga/scripts/create_kr260_ps_ddr_bd.tcl`: PS preset, HP0, clock,
  reset, and 1 GiB address assignment.
- `corev_apu/fpga/scripts/run_kr260_system_synth.tcl`: project creation,
  `validate_bd_design`, `generate_target`, and synthesis-only run with one job.

The Block Design contains only the PS, reset synchronization, reset inversion,
and constants required by the reset IP. It enables only `S_AXI_HP0_FPD` among
the PS-to-PL slave interfaces and disables unused PS AXI masters at the PL
boundary. It does not add Linux or PL Ethernet/USB/SPI/GPIO.

## What synthesis cannot prove

Even a successful integrated synthesis does not prove a working DDR access:

- PS boot firmware must initialize the DDR controller/PHY and enable PL clock
  and reset in the expected order.
- The Arm/PMU memory reservation policy must reserve the translated lower GiB
  for CVA6 before any concurrent PS software is used.
- JTAG pins still need an evidence-backed physical routing decision.
- Implementation timing, DRC, placement/routing, and board execution remain
  untested; this work intentionally runs none of those steps.
- The current ILA/VIO debug wrapper and PS/DDR system top are independently
  synthesized variants. Combining them for hardware capture is a later,
  explicit integration step.

The likely hardware bring-up sequence is PS-first: boot a minimal trusted PS
firmware/FSBL that initializes DDR and releases `pl_clk0`/`pl_resetn0`, then let
the CVA6 bootrom test run. That firmware and boot image are outside this RTL
prototype and are required before calling the design hardware-ready.
