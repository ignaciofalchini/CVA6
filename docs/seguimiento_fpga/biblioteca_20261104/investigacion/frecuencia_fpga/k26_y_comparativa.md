# K26 SOM fabric performance, PS PL clocking, and how fast other soft cores run (to place CVA6 at ~91 MHz on the KR260 in context)

Context (user data, not from external sources): unmodified CVA6 `cv64a6_imafdc_sv39` (RV64GC + double-precision FPU) on a KR260 (`xck26-sfvc784-2LV-c`), Vivado 2026.1, clocked from PS `pl_clk0` (IOPLL 999.99 MHz / 11 = 90.908 MHz). Timing closes at 90.9 MHz. At 100 MHz the best WNS is -0.553 ns, which puts the reachable frequency near 1/(10 + 0.553) ns, about **94.8 MHz**. Clock uncertainty is 0.142 ns (PS discrete jitter 0.276 ns). Critical paths have 28–39 logic levels with 60–65 % routing delay. On a VC707 (xc7vx485t-2) the official flow misses 50 MHz by -0.882 ns, which works out to about **47.9 MHz**.

---

## Q1. K26 speed grade and VCCINT, whether Vivado times it at 0.72 V, how -2LV at 0.72 V compares with other Zynq UltraScale+ grades, and whether the voltage can be changed

### Takeaway
The K26 uses a **-2 speed grade "LV" device that runs at VCCINT = 0.72 V**. In Vivado, "-2LV" is AMD's own label for a -2L part operated at 0.72 V. In the DS925 tables, fabric performance at 0.72 V is about **0.79–0.94× a standard -2 at 0.85 V**. It is roughly **equal to a -1 at 0.85 V** (block RAM is slightly worse, clock buffers slightly better). It is about **0.62–0.81× a -3 at 0.90 V**. Block RAM clock-to-out is hit hardest: +43 % versus -2 at 0.85 V. I found no AMD-supported way to run the K26 PL at 0.85 V.

### Cited Findings
- DS987 (K26 SOM data sheet, v1.2, 15 Mar 2022) says the SOM "leverages the XCK26-SFVC784-2LV-C/I, a custom-built Zynq UltraScale+ MPSoC that runs optimally (and exclusively) on the SOM". It comes in commercial (C) and industrial (I) grades. — [DS987 v1.2 (Sundance mirror)](https://www.sundance.com/wp-content/uploads/docs/k26-som-Data-Sheet.pdf)
- DS987 verbatim: "The K26 SOM is built with the XCK26-SFVC784-2LV device; which has a -2 speed grade and is an LV device (operates at VCCINT = 0.72V)." For data rates it refers to DS925. — [DS987 v1.2](https://www.sundance.com/wp-content/uploads/docs/k26-som-Data-Sheet.pdf)
- DS987 PS figures for the K26: APU (quad Cortex-A53) FMAX = 1333 MHz, RPU (Cortex-R5F) FMAX = 533 MHz, GPU (Mali-400 MP2) FMAX = 600 MHz. The PS_REF_CLK is a 33.33 MHz oscillator. — [DS987 v1.2](https://www.sundance.com/wp-content/uploads/docs/k26-som-Data-Sheet.pdf)
- DS987: the core rails are generated on the SOM. The SOM I2C map lists DA9062 (0x30/0x31), DA9130 (0x32) and DA9131 (0x33) PMICs. The carrier card defines only the PL **I/O** supplies (VCCO for HDIO/HPIO banks). — [DS987 v1.2](https://www.sundance.com/wp-content/uploads/docs/k26-som-Data-Sheet.pdf)
- DS925: Zynq UltraScale+ comes in -3, -2 and -1 speed grades, and -3E has the highest performance. "Some -2LE and -1LI devices can operate at a VCCINT voltage at 0.85V or 0.72V." At 0.85 V, "the speed specification for the L devices is the same as the -2I or -1I speed grades". At 0.72 V, "the -2LE and -1LI performance and static and dynamic power is reduced." — [DS925 Summary](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/Summary)
- DS925 Speed Grade Designations, footnote: the lowest-power -1L and -2L devices "where VCCINT = 0.72V, are listed in the Vivado Design Suite as -1LV and -2LV, respectively". The same L devices at 0.85 V are listed as -1L/-2L. XCK26 itself is not in the DS925 table, which covers XCZU/XAZU/XQZU only. — [DS925 Speed Grade Designations](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/Speed-Grade-Designations)
- DS925 Table 1 (available speed grades and voltages): -2LE at 0.72 V has VCCINT = 0.72 V while the PS domains (VCC_PSINTFP/LP etc.) stay at 0.85 V. — [DS925 Available Speed Grades and Operating Voltages](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/Available-Speed-Grades-and-Operating-Voltages)
- DS925 block RAM switching characteristics. Columns are 0.90 V -3 / 0.85 V -2 / 0.85 V -1 / **0.72 V -2** / 0.72 V -1, and the column mapping is unambiguous on this page. — [DS925 Block RAM and FIFO](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/Block-RAM-and-FIFO-Switching-Characteristics)
  - FMAX BRAM (WRITE_FIRST/NO_CHANGE): 825 / 738 / 645 / **585** / 516 MHz
  - FMAX BRAM (READ_FIRST) and ECC without pipeline: 718 / 637 / 575 / **510** / 460 MHz
  - TRCKO_DO (clock-to-out, no output register): 0.91 / 1.02 / 1.11 / **1.46** / 1.53 ns
  - TRCKO_DO_REG (with output register): 0.27 / 0.29 / 0.30 / **0.42** / 0.44 ns
- DS925 DSP48 FMAX ("with all registers used"), values in page order: 891 / 775 / 645 / 644 / 600 MHz. FMAX_PATDET: 794 / 687 / 571 / 562 / 524 MHz. The page flattening does not tie values to columns explicitly. — [DS925 DSP48 Slice Switching Characteristics](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/DSP48-Slice-Switching-Characteristics)
- DS925 global clock buffer FMAX (BUFG/BUFGCE/BUFGCE_DIV/BUFCE_LEAF), values in page order under the headers 0.90 V / 0.85 V / 0.72 V and grades -3, -2, -1, -2, -1: 891 / 775 / 667 / 725 / 667 MHz. BUFG_GT is 512 MHz in all columns. — [DS925 Clock Buffers and Networks](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/Clock-Buffers-and-Networks)
- DS925 shows the same LVDS/SelectIO rates in every speed/voltage column (e.g., HP LVDS DDR 1250 Mb/s). The 0.72 V penalty is a core-fabric effect, not an I/O one. — [DS925 PL Performance Characteristics](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/Programmable-Logic-PL-Performance-Characteristics)
- DS925 is currently at revision 1.30 (release date 2026-07-09). — [DS925 PL Switching Characteristics page metadata](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/Programmable-Logic-PL-Switching-Characteristics)

### Inferences
- **Vivado times xck26 -2LV at the 0.72 V characterization.** This is high confidence: DS987 says the part operates at 0.72 V, and DS925 defines "-2LV" in Vivado as the 0.72 V -2L device. The user can confirm from the timing report header (Speed File / Voltage) or with `report_property [get_parts xck26-sfvc784-2LV-c]`.
- **Ratios of -2LV at 0.72 V to other grades**, computed from the DS925 numbers above. For DSP and BUFG I mapped columns in the header order -3, -2, -1, -2(0.72), -1(0.72), which matches the unambiguous BRAM page:
  - vs **-2 at 0.85 V**: BRAM FMAX 0.79×, DSP 0.83×, BUFG 0.94×. BRAM clock-to-out is 1.46 vs 1.02 ns (+43 % delay, equivalent to 0.70× speed).
  - vs **-1 at 0.85 V**: BRAM 0.91×, DSP ~1.00×, BUFG 1.09×, BRAM clock-to-out 0.76×. **The K26 PL behaves roughly like a -1 (0.85 V) device**, slightly worse on BRAM paths and slightly better on clocking.
  - vs **-3 at 0.90 V**: BRAM 0.71×, DSP 0.72×, BUFG 0.81×, BRAM clock-to-out 0.62×.
- CVA6 critical paths often start or end at SRAM macros (cache data/tag arrays mapped to BRAM). The 0.72 V BRAM clock-to-out penalty (1.46 ns vs 1.02 ns at -2/0.85 V) eats a large share of a 10 ns cycle. It is likely one reason the K26 lands below 100 MHz. This is unverified: it should be checked against the actual critical-path start points.
- **Changing VCCINT is not supported, as far as I can find.** VCCINT is generated by on-SOM PMICs, the carrier only sets I/O rails, and AMD describes the device as one that "runs optimally (and exclusively) on the SOM" at 0.72 V. Raising VCCINT would be operation outside the device's rated condition. Vivado has no 0.85 V speed file to time against for xck26, though this is not directly verified (the user could check `get_parts xck26*`).

### Gaps
- I found no AMD statement on whether the K26 PMIC VCCINT setpoint can be changed, and no forum report of anyone doing it.
- DS925 CLB/LUT-level delays (e.g., TILO, carry) per voltage column were not retrievable from the HTML page, which was empty in fetch. BRAM, DSP and BUFG were used as fabric-speed proxies.
- UG1089/UG1091 were not consulted in detail. DS987 already settles the speed grade and voltage.

---

## Q2. PS PL clocks (pl_clk0..3): frequencies, PLL sources, jitter, and AMD guidance on using an MMCM

### Takeaway
pl_clk0..3 are integer divisions (two cascaded 6-bit dividers) of IOPLL, RPLL or DPLL. On the K26, PS_REF_CLK is 33.33 MHz, so IOPLL ≈ 999.99 MHz and **IOPLL/10 = 99.999 MHz is directly available**. AMD publishes no PS→PL output-jitter number that I could find, but Vivado models it as discrete jitter (0.276 ns in the user's design). Vivado's uncertainty works out to sqrt(TSJ² + DJ²)/2 + PE. Replacing the PS clock with an MMCM output (DJ of roughly 0.1–0.15 ns) would cut uncertainty from 0.142 ns to roughly 0.07 ns. That saves **about 0.07 ns, about 13 % of the 0.553 ns deficit at 100 MHz**: useful, but not enough on its own.

### Cited Findings
- PG201 (Zynq UltraScale+ PS IP): "PL side peripherals can be operated through a PL clock (FCLK_CLK0…3)", and these "generate the frequency ranges from 0.1 to 1600 MHz". — [PG201 Clocking](https://docs.amd.com/r/en-US/pg201-zynq-ultrascale-plus-processing-system/Clocking)
- UG1087 register reference for PL2_REF_CTRL (CRL_APB): SRCSEL selects 000 = IOPLL, 010 = RPLL, 011 = DPLL_CLK_TO_LPD. DIVISOR0 and DIVISOR1 are both 6-bit dividers in cascade. — [UG1087 PL2_REF_CTRL](https://docs.amd.com/r/en-US/ug1087-zynq-ultrascale-registers/PL2_REF_CTRL-CRL_APB-Register)
- UG1085 lists four PL clock outputs (PL_CLK0..3) from the PS clock subsystem. — [UG1085 TRM (AMD khub)](https://docs.amd.com/api/khub/documents/xzMsp_c5sG9J6A3u7NkJYQ/content?Ft-Calling-App=ft)
- DS925 PS clocks: PS_REF_CLK must be 27–60 MHz, with input RMS jitter ≤ 3 ps and period jitter ≤ 50 ps p-p (10,000 cycles). PS PLL output range is 750–1600 MHz, VCO 1500–3000 MHz, lock time ≤ 100 µs, the same for all speed grades. **No PL-clock output jitter figure is given on this page.** — [DS925 PS Clocks](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/PS-Clocks)
- K26 PS_REF_CLK is a 33.33 MHz oscillator. — [DS987 v1.2](https://www.sundance.com/wp-content/uploads/docs/k26-som-Data-Sheet.pdf)
- An AMD community answer citing UG1085 says the PS clock outputs are frequency references only and are not phase-aligned to each other. Phase-related clocks need a PL MMCM/PLL. — [AMD Adaptive Support: PS PLL clocks phase alignment](https://adaptivesupport.amd.com/s/question/0D52E00007FScjbSAD/zynq-mpsoc-ps-pll-clocks-phase-alignment?language=en_US)
- In a Xilinx forum thread on PS→PL clock jitter (for VCU pll_ref_clk), the user could not locate PS PLL output-jitter figures in DS925, and noted that UG572 describes the MMCM as usable as a jitter filter. — [Xilinx forum: PS to PL clock and VCU pll_ref_clk jitter](https://forums.xilinx.com:443/t5/Video-and-Audio/PS-to-PL-clock-and-VCU-pll-ref-clk-jitter/td-p/1043169)
- UG949 lists jitter filtering among the uses of an MMCM (clock-modifying blocks). — [UG949 Using Clock Modifying Blocks](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Using-Clock-Modifying-Blocks-MMCM-and-PLL)
- DS925 MMCM input jitter tolerance is < 20 % of the input clock period or 1 ns max. — [DS925 MMCM Switching Characteristics](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/MMCM-Switching-Characteristics)
- UG949 example (UltraScale, MMCM-generated 150 MHz clock): TSJ = 0.071 ns, DJ = 0.115 ns, PE = 0.120 ns, setup clock uncertainty = 0.188 ns. With a BUFGCE_DIV-derived clock, PE goes to 0 and uncertainty is 0.068 ns. — [UG949 Using BUFGCE_DIV to Reduce Clock Uncertainty](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Using-BUFGCE_DIV-to-Reduce-Clock-Uncertainty)
- UG906: clock uncertainty combines computed jitter (system, input, discrete), primitive phase error, and user uncertainty. For MMCM/PLL outputs, Vivado computes jitter from the source jitter and the MMCM/PLL configuration. — [UG906 Clock Uncertainty](https://docs.amd.com/r/2021.2-English/ug906-vivado-design-analysis/Clock-Uncertainty)
- UG903: the way input and system jitter combine into uncertainty "is not trivial and does not follow a single equation", and depends on path and topology. — [UG903 System Jitter](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints/System-Jitter)

### Inferences
- **Uncertainty formula, checked numerically.** The UG949 values reproduce exactly with U = sqrt(TSJ² + DJ²)/2 + PE: sqrt(0.071² + 0.115²)/2 = 0.0676, plus 0.120 = 0.188 ✓, and 0.068 without PE ✓. The user's numbers fit too: sqrt(0.071² + 0.276²)/2 = **0.1425 ns ≈ the reported 0.142 ns** ✓.
- **Expected MMCM benefit.** An MMCM-generated ~100 MHz clock with DJ of ~0.10–0.15 ns, and intra-clock paths with PE = 0, gives U ≈ 0.06–0.08 ns, a saving of ≈ 0.06–0.08 ns. That is only ~11–15 % of the -0.553 ns WNS at 100 MHz. The actual DJ depends on the MMCM M/D/O settings; the Clocking Wizard reports it.
- **Available frequencies.** IOPLL = 33.333 MHz × 30 ≈ 999.99 MHz, so the PS gives 999.99/(d0·d1): /9 = 111.1, /10 = **99.999**, /11 = 90.908, /12 = 83.33 MHz. Values in between (e.g., 92–95 MHz to sit exactly at the closure limit) need an MMCM fed from pl_clk0 or a board clock, or a different RPLL/DPLL setting. RPLL/DPLL also clock RPU/DisplayPort/etc., so reprogramming them has side effects.
- PG201's "0.1 to 1600 MHz" is the divider/PLL output range, not a usable fabric frequency. BUFG FMAX at 0.72 V -2 is ~725 MHz per DS925, and real logic is far below either limit.
- The PS-derived clock is not inherently a timing blocker. It costs ~0.07 ns more uncertainty than an MMCM, which matters only at the margin, for example when WNS at 100 MHz is between about -0.07 and 0 ns.

### Gaps
- I could not find an official DS925/UG1085 figure for PL_CLKx output jitter (period or cycle-to-cycle). The 0.276 ns DJ is Vivado's internal model value.
- I found no explicit AMD statement saying "use an MMCM rather than pl_clk for high-frequency fabric logic". Only the general guidance (MMCM for jitter filtering and phase alignment) was found.

---

## Q3. Reported frequencies of other Linux-capable RISC-V soft cores and MicroBlaze/MicroBlaze V on Zynq UltraScale+ and 7-series (comparison table)

### Takeaway
Wherever both are reported on the same 7-series board, **CVA6 runs at about half the frequency of Rocket.** CVA6's official and published FPGA builds target **25–50 MHz** on 7-series and **50 MHz** on a ZCU102. Rocket reaches **~100 MHz on VC707** and **~180–195 MHz on ZCU102 (-2, 0.85 V)**. FPGA-oriented cores (VexRiscv, NaxRiscv, MicroBlaze V) run at **150–260 MHz**. Against that, ~91–95 MHz for an unmodified RV64GC CVA6 with a DP-FPU on a 0.72 V -2LV part is consistent with what others report, if anything at the good end.

### Cited Findings (comparison table)

"Type" says what the number is: **met** = timing closed, **target/default** = the build's clock setting (not necessarily the Fmax), **max** = maximum reported by the authors, **synth** = synthesis/standalone estimate.

| Core / configuration | ISA, FPU | Device / grade (VCCINT) | Freq. | Type | Source |
|---|---|---|---|---|---|
| **CVA6 cv64a6_imafdc_sv39 (user)** | RV64GC, DP-FPU | KR260 xck26-2LV (0.72 V) | 90.9 MHz met; 100 MHz WNS -0.553 (~94.8 MHz est.) | met | user data |
| **CVA6 same (user)** | RV64GC, DP-FPU | VC707 xc7vx485t-2 | 50 MHz fails by -0.882 ns (~47.9 MHz est.) | met/est. | user data |
| CVA6 CORE-V APU (official FPGA flow) | RV64GC | Genesys 2 (Kintex-7 xc7k325t-2) | 50 MHz | target | [DeepWiki CVA6 FPGA summary (third-party, from bootrom Makefile)](https://deepwiki.com/openhwgroup/cva6/7.2-fpga-implementation) |
| CVA6 (other board in same summary) | — | Nexys Video (Artix-7) | 25 MHz | target | [DeepWiki](https://deepwiki.com/openhwgroup/cva6/7.2-fpga-implementation) |
| CVA6 | RV64/RV32 | Arty A7-100T | 25 MHz | target | [CVA6 MR (search snippet, not opened)](https://gitlab.eclipse.org/openhw-group/backup-20241120/cva6/-/merge_requests/2581) |
| CVA6-based RT MCU (Cuomo et al., ETH/Huawei) | RV64GC | ZCU102 (XCZU9EG, Zynq US+) | "targeting 50 MHz" | target | [arXiv 2307.04148](https://arxiv.org/pdf/2307.04148) |
| Rocket (rc-fpga-zcu, fpga-zynq port) | RV64 (FPU not stated) | ZCU102 xczu9eg-2 (0.85 V) | "can reach 195 MHz" single-core, Vivado 2017.1 | max | [li3tuo4/rc-fpga-zcu](https://github.com/li3tuo4/rc-fpga-zcu) |
| Rocket (same port, fork) | RV64 | ZCU102 | "180 MHz at maximum" | max | [ncppd/rc-fpga-zcu (search snippet)](https://github.com/ncppd/rc-fpga-zcu) |
| Rocket (Chipyard RocketVCU118Config) | RV64GC (Rocket default) | VCU118 (XCVU9P, Virtex US+) | 100 MHz ("default 100MHz freq") | default | [Chipyard VCU118 docs](https://chipyard.readthedocs.io/en/main/prototyping/vcu118/) |
| Rocket (vivado-risc-v, rocket64bN) | RV64GC, "configured to include floating point" | VC707 (Virtex-7) | "up to 100MHz clock speed", up to 8 cores | max/default | [vivado-risc-v README](https://github.com/eugene-tarassov/vivado-risc-v/blob/master/README.md) |
| Rocket (vivado-risc-v) | RV64GC | KC705, Genesys 2 (Kintex-7) | "as fast as VC707" (~100 MHz), up to 4 cores | max/default | [vivado-risc-v README](https://github.com/eugene-tarassov/vivado-risc-v/blob/master/README.md) |
| Rocket (vivado-risc-v) | RV64GC | Nexys Video (Artix-7) | up to 50 MHz, 2 cores | max/default | [vivado-risc-v README](https://github.com/eugene-tarassov/vivado-risc-v/blob/master/README.md) |
| Rocket (vivado-risc-v) | RV64GC | Arty A7-100T / Nexys A7-100T | 50 MHz, 1 core | default | [vivado-risc-v README](https://github.com/eugene-tarassov/vivado-risc-v/blob/master/README.md) |
| Rocket supernode (FireSim) | RV64GC | AWS F1 (VU9P) | F85MHz platform config | target | [FireSim commit mirror (search snippet only)](https://cdn05042023.gitlink.org.cn/replica/firesim/commit/44b56ad23e2e325f7a7569d29b5027a7efba4442) |
| BOOM single-core (FireSim) | RV64GC | AWS F1 (VU9P) | F75MHz platform config | target | [FireSim commit mirror (search snippet only)](https://cdn05042023.gitlink.org.cn/replica/firesim/commit/44b56ad23e2e325f7a7569d29b5027a7efba4442) |
| BOOM (FireSim) | RV64GC | AWS F1 FPGAs | "90+ MHz" | claim | [older BOOM README (fork)](https://github.com/sxu55/riscv-boom) |
| BOOM (vivado-risc-v) | RV64GC, 1–4-wide | VC707/KC705/Genesys 2 | no per-config MHz given | — | [vivado-risc-v README](https://github.com/eugene-tarassov/vivado-risc-v/blob/master/README.md) |
| NaxRiscv (high-perf config, 13.3 kLUT) | RV32/RV64 IMAFDCSU supported; benchmark config not stated | Artix-7 "-3" | 155 MHz | max (author) | [NaxRiscv README](https://github.com/SpinalHDL/NaxRiscv) |
| VexRiscv "Linux balanced" (MMU, S-mode) | RV32IMA, no FPU | Artix-7 fastest grade | 180 MHz (2883 LUT) | synth (core as toplevel) | [VexRiscv README](https://github.com/SpinalHDL/VexRiscv) |
| VexRiscv "Full with MMU" | RV32IM | Artix-7 fastest grade | 151 MHz | synth | [VexRiscv README](https://github.com/SpinalHDL/VexRiscv) |
| VexRiscv-SMP (Linux-on-LiteX) | RV32IMA (+opt. FPU) | ZCU104 xczu7ev-2 / KCU105 / VC707 / KC705 | 125 MHz | default | [litex-boards xilinx_zcu104.py](https://github.com/litex-hub/litex-boards/blob/master/litex_boards/targets/xilinx_zcu104.py), [Linux-on-LiteX boards.py](https://github.com/litex-hub/linux-on-litex-vexriscv) |
| VexRiscv-SMP (Linux-on-LiteX) | RV32IMA | Genesys 2 | 100 MHz | default | [litex-boards digilent_genesys2.py](https://github.com/litex-hub/litex-boards/blob/master/litex_boards/targets/digilent_genesys2.py) |
| VexRiscv-SMP (Linux-on-LiteX) | RV32IMA | Alveo U280 (with HBM) | 250 MHz | default | [Linux-on-LiteX boards.py](https://github.com/litex-hub/linux-on-litex-vexriscv) |
| **MicroBlaze V "Linux" preset** | RV64IMAFDC, MMU, FPU | Zynq US+ XCZU9EG ffvb1156 **-3** | **258 MHz** | AMD table | [UG1629 Resource Utilization](https://docs.amd.com/r/en-US/ug1629-microblaze-v-user-guide/Resource-Utilization) |
| MicroBlaze V Linux | RV64IMAFDC | Kintex US+ XCKU15P -3 / Virtex US+ XCVU3P -3 | 258 / 257 MHz | AMD table | [UG1629](https://docs.amd.com/r/en-US/ug1629-microblaze-v-user-guide/Resource-Utilization) |
| MicroBlaze V Linux | RV64IMAFDC | Kintex-7 XC7K325T -3 / Virtex-7 XC7VX485T -3 | 155 / 141 MHz | AMD table | [UG1629](https://docs.amd.com/r/en-US/ug1629-microblaze-v-user-guide/Resource-Utilization) |
| MicroBlaze V Linux | RV64IMAFDC | Zynq-7000 XC7Z020 -3 / Artix-7 XC7A200T -3 / Spartan-7 XC7S25 -2 | 101 / 102 / 90 MHz | AMD table | [UG1629](https://docs.amd.com/r/en-US/ug1629-microblaze-v-user-guide/Resource-Utilization) |
| MicroBlaze V Linux | RV64IMAFDC | Artix US+ XCAU25P -2 / Spartan US+ XCSU35P -2 / Versal XCVC1902 -3HP | 219 / 199 / 248 MHz | AMD table | [UG1629](https://docs.amd.com/r/en-US/ug1629-microblaze-v-user-guide/Resource-Utilization) |
| MicroBlaze V "Application" preset | RV32IMAFC, FPU | ZU9EG -3 / K7 -3 / V7 -3 | 264 / 168 / 160 MHz | AMD table | [UG1629](https://docs.amd.com/r/en-US/ug1629-microblaze-v-user-guide/Resource-Utilization) |
| MicroBlaze V "Microcontroller" preset (lower-bound reference) | RV32IMC | ZU9EG -3 / K7 -3 / V7 -3 | 400 / 244 / 234 MHz | AMD table | [UG1629](https://docs.amd.com/r/en-US/ug1629-microblaze-v-user-guide/Resource-Utilization) |
| MicroBlaze V max per family (fastest grade) | — | Zynq US+ / Kintex US+ / Virtex US+ | 526 / 535 / 524 MHz | AMD table | [UG1629 2024.1 Maximum Frequencies](https://docs.amd.com/r/2024.1-English/ug1629-microblaze-v-user-guide/Maximum-Frequencies) |
| Classic MicroBlaze max per family (fastest grade) | — | Zynq US+ 661, Kintex US+ 650, Virtex US+ 682, Kintex-7 398, Virtex-7 382, Artix-7 267, Zynq-7000 265 MHz | — | AMD table | [UG984 Maximum Frequencies](https://docs.amd.com/r/en-US/ug984-vivado-microblaze-ref/Maximum-Frequencies) |

Supporting qualitative and CVA6-specific findings:
- Thales (OpenHW, May 2022): "CVA6 initially designed for ASIC targets". CV32A6 was "being optimized to also be an FPGA soft-core", with "+50% frequency achieved" and "-30% resources achieved". These are 32-bit CV32A6 FPGA optimizations, and the board and baseline MHz are not stated. — [Thales slides, Open-Source SoC RISC-V meeting 2022](https://open-src-soc.org/2022-05/media/slides/4th-RISC-V-Meeting-2022-05-04-14h55-J%C3%A9r%C3%B4me-Qu%C3%A9vremont.pdf)
- A CVA6 FPGA-optimized register file (LUTRAM) MR on xc7k325tffg900-2 cut LUTs from 40,499 to 36,350 and FFs from 22,799 to 18,806, using 440 LUTRAM. No frequency figure was reported in the snippet. — [CVA6 MR 497](https://gitlab.eclipse.org/openhw-group/backup-20241120/cva6/-/merge_requests/497)
- CVA6 RESOURCES.md lists FPGA platforms: Genesys 2 (default APU board for the OS ports), Zybo Z7-20 (student contest kits), and "CVA6-MPSoC" for AMD PYNQ-Z2 and **ZCU104**, which boots Linux 6.6. No MHz is stated. — [CVA6 RESOURCES.md](https://github.com/openhwgroup/cva6/blob/master/RESOURCES.md)
- Cheshire (PULP SoC around CVA6) ships FPGA setups for Genesys 2, VCU118 and VCU128. The docs page states no clock frequency. — [Cheshire Xilinx docs](https://pulp-platform.github.io/cheshire/tg/xilinx/)
- BOOM README: "While BOOM is primarily ASIC-optimized, it is also usable on FPGAs." — [riscv-boom README](https://github.com/riscv-boom/riscv-boom)
- NaxRiscv README: the design aims for "high fmax (not the best IPC)", and Xilinx series 7 is the reference target so far. — [NaxRiscv README](https://github.com/SpinalHDL/NaxRiscv)
- MicroBlaze V presets (UG1629 Table 14): Linux = RV64IMAFDC, C_USE_MMU=3, C_USE_FPU=2. LUT/FF on ZU9EG: 14,994 LUT / 7,504 FF / 16 BRAM36 / 6 DSP. — [UG1629](https://docs.amd.com/r/en-US/ug1629-microblaze-v-user-guide/Resource-Utilization)
- Dörflinger et al., "A comparative survey of open-source application-class RISC-V processor implementations" (ACM CF'21, DOI 10.1145/3457388.3458657), compares Rocket, BOOM, CVA6 and SHAKTI C-Class on identical **Virtex UltraScale+** platforms and GF22FDX. It reports up to 3.1× differences between implementations. **Its MHz values could not be retrieved** (the PDF was behind a bot check). — [Uni Lübeck record](https://research.uni-luebeck.de/en/publications/a-comparative-survey-of-open-source-application-class-risc-v-proc/)
- A preprint (single author, a 32-bit 5-stage RISC-V on Kintex UltraScale XQRKU060, not CVA6) reports FPGA critical-path routing at **~62–74 % of path delay (avg ~68 %)**, versus 20–35 % in a 7 nm ASIC. This is low-confidence context: unreviewed, and a different core. — [arXiv 2512.13866](https://arxiv.org/pdf/2512.13866)

### Inferences
- **CVA6 vs Rocket on the same board.** On VC707, Rocket with FPU builds run at up to 100 MHz (vivado-risc-v), while the user's CVA6 reaches ~48 MHz. On Zynq US+ -2 (ZCU102), Rocket reaches 180–195 MHz, while CVA6 builds target 50 MHz (published) and ~95 MHz (user, on the slower -2LV part). **CVA6 consistently comes in at about 0.5× Rocket's frequency on the same fabric.** This fits a core described by its own maintainers as ASIC-first, and the user's long logic paths (28–39 levels) and routing-dominated delay.
- **Normalizing to the K26 grade** with the DS925 ratios from Q1:
  - MicroBlaze V Linux preset (RV64IMAFDC + MMU + FPU) at 258 MHz on ZU+ -3 scales to **~183–204 MHz on -2LV/0.72 V** (×0.71–0.79). CVA6 at ~91–95 MHz is therefore ~2× below AMD's FPGA-native RV64GC core.
  - Rocket at 180–195 MHz on ZU9EG -2/0.85 V would scale to ~150–180 MHz on the K26 (×0.79–0.94). This is speculative: the FPU status of that build is not stated, and it was Vivado 2017.1.
  - CVA6's ~94.8 MHz on -2LV would correspond to **~100–120 MHz on a standard -2/0.85 V Zynq US+** such as the ZCU104/ZCU102 (÷0.79–0.94), and roughly the same as now on a -1 (0.85 V) part.
- A 64-bit core with a DP-FPU, MMU and 6 stages, and no FPGA-specific RTL work, is expected to sit far below the 32-bit FPGA-native cores in this table (VexRiscv, NaxRiscv, MicroBlaze V App/MC presets). Those are lower-bound and reference points, not like-for-like comparisons.
- The user's 60–65 % routing share is within the typical FPGA range. The only quantitative source found is the low-confidence preprint above, at 62–74 %.

### Gaps
- **No published CVA6 Fmax (timing-closed maximum) on any UltraScale+ device was found.** Only targets were found: 50 MHz on ZCU102, and Cheshire/VCU118/VCU128 without MHz. The Dörflinger CF'21 survey probably contains Virtex US+ frequencies for Rocket, BOOM and CVA6, but could not be accessed.
- CVA6-MPSoC (ZCU104) and the COMPAS'25 tutorial pages, which might state a CVA6 MHz on ZCU104, returned 404.
- FireSim F75/F85 MHz values come from a search snippet of a mirrored commit, and the "90+ MHz" BOOM figure comes from an old README in a fork. Neither was verified on the current FireSim/BOOM repos.
- Whether the rc-fpga-zcu 195 MHz Rocket build includes an FPU is not stated.
- No Ibex/CV32E40P Fmax numbers were collected. VexRiscv-small (243 MHz Artix-7, RV32I) and the MicroBlaze V Microcontroller preset (400 MHz ZU+ -3) serve as lower-bound references instead.
- No NaxRiscv or VexRiscv-SMP timing-closed numbers on UltraScale+ were found. The LiteX 125 MHz values are board-target defaults, not measured Fmax, and are for the 32-bit VexRiscv-SMP.

---

## Q4. Rule of thumb: how much faster UltraScale+ fabric is than 7-series for the same design

### Takeaway
AMD's own like-for-like MicroBlaze V and MicroBlaze tables (same RTL, fastest grade of each family) show **UltraScale+ ≈ 1.4–1.8× Kintex-7/Virtex-7** and **≈ 2.5× Artix-7-class fabric (including Zynq-7000 Z-7020)**. After accounting for the K26's 0.72 V penalty, the expected K26 (-2LV) advantage over a Virtex-7 -2 (VC707) is about **1.3–1.5×**. The user's measured CVA6 ratio (~94.8/~47.9 ≈ **1.98×**) is higher than this.

### Cited Findings
- MicroBlaze V Linux preset (RV64IMAFDC): Kintex-7 -3 = 155 → Kintex US+ -3 = 258 MHz; Virtex-7 -3 = 141 → Virtex US+ -3 = 257 MHz; Zynq-7000 (Z-7020) -3 = 101 → Zynq US+ -3 = 258 MHz. — [UG1629 Resource Utilization](https://docs.amd.com/r/en-US/ug1629-microblaze-v-user-guide/Resource-Utilization)
- MicroBlaze V Application preset (RV32IMAFC + FPU): K7 168 → KU+ 241; V7 160 → VU+ 268; ZU+ 264 MHz. Microcontroller preset: K7 244 → KU+ 420; V7 234 → VU+ 379. Maximum Frequency preset: K7 359 → KU+ 558; V7 320 → VU+ 540. — [UG1629](https://docs.amd.com/r/en-US/ug1629-microblaze-v-user-guide/Resource-Utilization)
- Classic MicroBlaze maximum frequency (fastest grade): Kintex-7 398 → Kintex US+ 650; Virtex-7 382 → Virtex US+ 682; Zynq-7000 265 → Zynq US+ 661 MHz. — [UG984 Maximum Frequencies](https://docs.amd.com/r/en-US/ug984-vivado-microblaze-ref/Maximum-Frequencies)
- DS925 speed-grade data for the 0.72 V penalty is listed in Q1. — [DS925 Block RAM](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/Block-RAM-and-FIFO-Switching-Characteristics)

### Inferences
- Ratios computed from the AMD tables above, same RTL and fastest grades:
  - Linux preset: KU+/K7 = 1.66×, VU+/V7 = 1.82×, ZU+/Z-7020 = 2.55×, ZU+/A7 = 2.53×.
  - Application preset (with FPU): KU+/K7 = 1.43×, VU+/V7 = 1.68×, ZU+/K7 = 1.57×.
  - Microcontroller and MaxF presets: 1.55–1.72×.
  - Classic MicroBlaze: KU+/K7 = 1.63×, VU+/V7 = 1.79×, ZU+/Z7 = 2.49×.
  - **Rule of thumb: ~1.6–1.8× vs Kintex/Virtex-7, ~2.5× vs Artix-7/Zynq-7000, at equal (top) speed grade.**
- **Applying it to the K26.** The K26's -2LV at 0.72 V is ~0.71–0.81× a ZU+ -3 (DS925). Comparing against a Virtex-7 -3, the expected ratio is 1.82 × (0.71–0.81) ≈ 1.3–1.5×. The VC707 is a -2 part, so the expected K26/VC707 ratio would be somewhat higher: the 7-series -2 vs -3 gap was not sourced here (DS183). The user's measured ~1.98× is above this estimate. Possible reasons, all unverified:
  - The VC707 run used the official CVA6 FPGA flow (different SoC wrapper, constraints, strategies, Vivado version), not an identical netlist.
  - The xc7vx485t is a large die, so placement may be spread out.
  - Single-run WNS-based Fmax estimates are noisy.
  - Either way, both results point the same direction: the K26 result is not anomalously low.
- The routing-dominated, deep-logic critical paths are typical of ASIC-oriented RTL on FPGAs. UltraScale+ routing improvements (vs 7-series) help, but cannot make up for 28–39 LUT levels. Reaching 100 MHz on the K26 likely needs RTL/microarchitectural work (e.g., FPU pipelining, cache/BRAM output registering, the CVA6 FPGA-optimization options), not just clocking changes.

### Gaps
- I found no AMD white paper that gives a single official "UltraScale+ is N× faster than 7-series" figure for user logic. The ratios above are derived from AMD's soft-processor tables.
- 7-series -2 vs -3 scaling (DS183/DS182) was not retrieved, so the VC707 (-2) normalization is approximate.

---

## Q5. Overall judgment: is ~91 MHz reasonable for a 64-bit CVA6 with FPU on a KR260?

### Takeaway
**Yes. ~91 MHz (≈95 MHz achievable) is a reasonable, even good, result** for unmodified `cv64a6_imafdc_sv39` on the K26's -2LV/0.72 V fabric. It is ~2× the frequencies used by CVA6's official 7-series flows (25–50 MHz) and the published ZCU102 CVA6 design (50 MHz). It is in line with CVA6's ~0.5× ratio to Rocket on the same fabric. An MMCM would gain only ~0.07 ns, so closing 100 MHz would mostly need RTL changes, or a standard -2/0.85 V Zynq US+ part (estimated ~100–120 MHz).

### Cited Findings
- K26 = -2 speed grade LV device at VCCINT 0.72 V. — [DS987 v1.2](https://www.sundance.com/wp-content/uploads/docs/k26-som-Data-Sheet.pdf)
- At 0.72 V, L-device performance is reduced versus 0.85 V. — [DS925 Summary](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/Summary)
- CVA6 FPGA targets: Genesys 2 50 MHz, Nexys Video 25 MHz ([DeepWiki](https://deepwiki.com/openhwgroup/cva6/7.2-fpga-implementation)); CVA6 MCU on ZCU102 "targeting 50 MHz" ([arXiv 2307.04148](https://arxiv.org/pdf/2307.04148)).
- Rocket: VC707 up to 100 MHz ([vivado-risc-v](https://github.com/eugene-tarassov/vivado-risc-v/blob/master/README.md)); ZCU102 up to 195 MHz single core ([rc-fpga-zcu](https://github.com/li3tuo4/rc-fpga-zcu)).
- "CVA6 initially designed for ASIC targets" — [Thales 2022 slides](https://open-src-soc.org/2022-05/media/slides/4th-RISC-V-Meeting-2022-05-04-14h55-J%C3%A9r%C3%B4me-Qu%C3%A9vremont.pdf)

### Inferences
- Levers, ranked by expected impact on the K26:
  1. **Microarchitectural/RTL changes.** Examples: register BRAM outputs, given BRAM clock-to-out of 1.46 ns at 0.72 V; deepen FPU pipelining; use CVA6 FPGA-friendly options (LUTRAM regfile etc.). Thales reports +50 % frequency from FPGA optimizations on CV32A6.
  2. **Implementation strategies.** Performance_Explore/ExtraTimingOpt, phys_opt, retiming. These are plausible for the last ~0.5 ns but unquantified here.
  3. **Clock source.** MMCM instead of pl_clk0 saves ≈0.07 ns of uncertainty (computed). Alternatively, use an MMCM to run at ~93–95 MHz instead of the 90.9 MHz forced by the IOPLL /11 divider.
- Do not expect the same core to close 100 MHz on the K26 without design changes. On a standard -2 (0.85 V) Zynq US+ board it likely would (estimate only).

### Gaps
- No independent published CVA6 Fmax on any UltraScale+ part could be found to anchor the estimate directly. See the Q3 gaps.
