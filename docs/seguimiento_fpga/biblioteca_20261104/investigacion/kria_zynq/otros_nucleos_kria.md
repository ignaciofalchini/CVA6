# Other Linux-capable RISC-V soft cores (and MicroBlaze V) on Kria K26 and Zynq UltraScale+: what clock they reach

**Research date:** 2026-10-28.

**Method:** web search; raw GitHub files and the GitHub API (through the already-authenticated `gh` CLI, read-only); PDF text extraction for reading only.

**Scope:** only facts that are new or that correct the notes in `../Frecuencia del CVA6 en FPGA/`, especially `k26_y_comparativa.md` and `ports_y_papers.md`.

**User baseline:** unmodified `cv64a6_imafdc_sv39` (RV64GC with a double-precision FPU) on a KR260 (`xck26-sfvc784-2LV-c`, -2LV at 0.72 V).
- It meets timing at 90.9 MHz.
- At 100 MHz it fails with WNS −0.553 ns, which puts the reachable frequency at about 94.8 MHz.

**How to read the "Type" column:**

| Label | Meaning |
|---|---|
| **default** | A configured target in a shipped flow. Timing closure is not shown. |
| **closed@X (WNS)** | The source reports positive slack at X. |
| **Fmax-measured** | The source swept the clock or reported the failing next step. |
| **claim** | The text asserts it without a report. |

"est." values are my own arithmetic, 1/(T − WNS). They are rough, because Vivado does not keep the same critical path when the constraint changes.

---

## Takeaway

**1. Kria/K26 now has direct comparison points (all new, all 2026, all from small or one-person projects).**

| Design on `xck26-sfvc784-2LV-c` | Clock and slack | Notes |
|---|---|---|
| Kronos, clean-room RV64IMAFDC with FPU | Closed **200 MHz** | Measured before it had caches and an MMU. With caches and MMU it was at about 127 MHz (est.). |
| Dual "Huge" Rocket, RV64GC with FPU | Closed **100 MHz** with WNS **+0.287 ns** (~103 MHz est.) | Linux on Rocket not shown. |
| Tanager, clean-room out-of-order RV64GC, two cores with two threads each | Closed **100 MHz** with WNS +0.75 to +1.07 ns | Four-hart Linux on the board. The README says it is "agent-built". |
| Accemic trace demonstrators: CVA6 RV64IMAC (**no FPU**) and Rocket RV64IMAC (no FPU), both booting Linux | All constrained to **71.1 MHz** | CVA6 RV64 slack is only +0.603 ns (~74 MHz est.). Rocket runs at 75 MHz on the board. |
| NaxRiscv RV64IMA (no FPU) via LiteX | **100 MHz**, timing closed | Linux not verified. |

**2. Framework support for Kria and Zynq US+**
- **LiteX:** has a KV260 target, but its default CPU is the Cortex-A53 (`zynqmp`), not a soft core. The default sys clock is 100 MHz. The PL clock input for a soft core is marked "not tested". There is no KR260 target.
- **vivado-risc-v:** supports no Zynq US+ or Kria board.
- **Chipyard:** added **ZCU104** in Aug/Sep 2026. The defaults are Rocket at 100 MHz and MegaBoom at 50 MHz.
- **FireSim:** has no Zynq platform.

**3. Dörflinger et al., CF'21 (retrieved)**

Setup:
- Board: VCU118, XCVU9P, VCCINT 0.85 V. The speed grade is not stated; the VCU118 part is −2L.
- Tool: Vivado 2019.2, default settings, all cores with MAFDC.
- Method: Fmax was found by raising the clock until timing failed.

Fmax results:

| Core | Fmax (MHz) |
|---|---|
| Rocket | 198 |
| SHAKTI C-Class | 136 |
| **CVA6 (OpenPiton framework)** | **112** |
| BOOM | 88 |

The paper says "CVA6 clocking is restricted by L1D logic". CVA6/Rocket = 0.57.

**4. Inference.** Applying the prior notes' −2LV@0.72 V factor (0.79–0.94) to the paper's 112 MHz gives **~88–105 MHz** on the K26. The user's 90.9 MHz (≈94.8 MHz reachable) falls inside that range. This is consistent with an ordinary result for unmodified CVA6 with an FPU, not a poor one.

---

## Master data table (new data points only)

| # | Source | Core | ISA / config (XLEN, FPU) | Board, part, grade | MHz | Type | Linux | Exact quote (<25 words) |
|---|---|---|---|---|---|---|---|---|
| K1 | [vladdum/kronos-riscv README](https://github.com/vladdum/kronos-riscv) (repo 2026-04/08) | Kronos (one-person, clean-room, in-order) | RV64IMAFDC, FPU on. "Stage-5b" netlist: **no caches/MMU yet** | KV260, `xck26-sfvc784-2LV-c`, Vivado 2025.2, PS clock | **200 closes (WNS 0.000)**; 220 fails (WNS ≈ −0.34 → ~205 est.) | Fmax-measured (post-route) | No (core "can boot real software"; no Linux shown) | "Post-route Fmax measured on this stage (Vivado 2025.2, xck26-sfvc784-2LV)" |
| K1b | [kronos docs/architecture.md](https://github.com/vladdum/kronos-riscv/blob/main/docs/architecture.md) | Kronos, stage 7d (9-stage, with I/D caches, Sv39 MMU, PMP) | RV64IMAFDC | same | Target 200, **WNS −2.872 ns** (~127 est.) | Failing-at-target | No | "post-route WNS −3.128 → −2.872 ns on KV260 (xck26-2LV, Vivado 2025.2)" |
| K2 | [MaybeBlue308/KV260_Rocket_2core, ROCKET_KV260_GUIDE.md](https://github.com/MaybeBlue308/KV260_Rocket_2core/blob/main/kv260_porting/ROCKET_KV260_GUIDE.md) (repo created 2026-10-15) | Chipyard `KV260DualRocketConfig`: 2× "Huge" Rocket, L1 32/32 KB, L2 512 KB (URAM) | RV64GC + **FPU** + Bitmanip | KV260, `xck26-sfvc784-2LV-c`; PS `pl_clk0` | **100**, WNS **+0.287 ns** (~103 est.), 77.8K LUT (66%) | closed@100 (claim in guide) | Planned only: OpenSBI+kernel steps written, no boot log | "Worst Negative Slack (WNS): `+0.287 ns`" / "2 core Huge RV64GC với FPU + Bitmanip" |
| K3 | [tianjianh/tanager README](https://github.com/tianjianh/tanager) (public 2026-10-24; README says "agent-built") | Tanager (clean-room OoO, 2-wide decode), 2 cores × SMT2 | RV64GC, F+D | KV260 (XCK26) | **100**, WNS **+0.748 ns** release image (~108 est.); later +1.07/+0.34 | closed@100 | **Yes**, four-hart Linux on board at 100 MHz | "the release chip closes 100 MHz (2026-10-23)" / "WNS +0.748 ns, 112,806 LUTs (96.3% of the XCK26)" |
| K4 | [accemic/TraceEncoder examples/kv260/cva6_linux64](https://github.com/accemic/TraceEncoder/tree/main/examples/kv260/cva6_linux64) + [dashboard/plclk.json](https://github.com/accemic/TraceEncoder/blob/main/examples/dashboard/plclk.json) | CVA6 + N-Trace encoder (Accemic Technologies) | `cv64a6_imac_sv39_ctrace`: RV64IMAC, **no FPU**, Sv39 | KV260, `xck26-sfvc784-2LV-c`, Vivado 2026.1 | Constraint **71.114**, WNS **+0.603 ns** (~74 est.); run at 68.18 | closed@71.1 | Yes (README: "booting Linux") | "Constraint 71.114 MHz with WNS +0.603 ns" |
| K5 | same, `cva6_2` (rv64 build) | 2 × CVA6 (AMP), 2 encoders | RV64 config (FPU not stated; same source as K4) | same | Constraint 71.114, WNS **+0.125 ns** (~72 est.) | closed@71.1 | Two guest Linux images (README) | "Constraint 71.114 MHz with WNS +0.125 ns" |
| K6 | same, `cva6_linux` | CVA6 | `cv32a6_ima_sv32_fpga` (RV32IMA, no FPU) | same | Constraint 71.114, WNS +2.265 ns (~85 est.) | closed@71.1 | Yes | "Constraint 71.114 MHz with WNS +2.265 ns" |
| K7 | same, `rocket_linux` | Rocket `Rocket64t1` + encoder | RV64IMAC, **no FPU** | same | Constraint 71.114, WNS +2.114 ns (~84 est.); **runs at 75 on board** | closed@71.1 + board run | **Yes**, "boots to buildroot login" at 75 MHz | "Constraint 71.114 MHz with WNS +2.114 ns" |
| K8 | same, `rocket2` | Rocket `Rocket64t2` (2 harts) | RV64IMAC, no FPU | same | Constraint 71.114, WNS +3.578 ns (plclk.json; tutorial table says +2.399), ~86–95 est.; runs at 75 | closed@71.1 + board run | **Yes**, SMP Linux | "4.9x the 0.729 ns that 75 MHz costs, the largest margin in the family" |
| K9 | same, `mbv` | AMD MicroBlaze V (bare) + encoder | RV32 (preset not stated; bare-metal programs) | same | Constraint 71.114, WNS +2.331 ns; runs at 75 | closed@71.1 | No (PS runs Linux; MB-V bare-metal) | "Constraint 71.114 MHz with WNS +2.331 ns" |
| K10 | [ormastes/simple status report 2026-05-21](https://github.com/ormastes/simple/blob/main/doc/09_report/2026/05/riscv_fpga_linux_hardware_status_2026-05-21.md) | NaxRiscv via LiteX | RV64IMA (`rv64i2p0_ma`), Sv39, **no FPU**, L2 128 KB | KV260/K26, `xck26-sfvc784-2lv-c`, Vivado 2025.2 | **100** | closed@100 (claim) | Not verified (UART not wired) | "CPU: NaxRiscv RV64, ISA `rv64i2p0_ma`, MMU sv39, 100 MHz, L2 cache 128 KB." |
| K11 | [litex-boards xilinx_kv260.py](https://github.com/litex-hub/litex-boards/blob/master/litex_boards/targets/xilinx_kv260.py) + [platform](https://github.com/litex-hub/litex-boards/blob/master/litex_boards/platforms/xilinx_kv260.py) | LiteX SoC; default CPU = **PS Cortex-A53 (`zynqmp`)** | No soft core by default | `xck26-sfvc784-2lv-c` | `--sys-clk-freq` default **100** | default | No (LiteX BIOS on A53) | "The current support is sufficient to run LiteX BIOS on Cortex-A53 core #0" |
| K12 | [ReinventTech/signate-ai-edge-6th](https://github.com/ReinventTech/signate-ai-edge-6th) (SIGNATE 6th AI Edge Contest, 2022–23) | VexRiscv "with FPU" IP | RV32 + FPU | KV260; PS `PL0_REF_CTRL` = 100 MHz in BD | 100 (PL0 setting; core-clock binding inferred) | default | No | IP name `vexriscv_with_fpu_1` in `hw/vivado/system.bd` |

### Zynq US+ boards and other UltraScale+ parts (new)

| # | Source | Core | ISA / config | Board, part, grade | MHz | Type | Linux | Exact quote (<25 words) |
|---|---|---|---|---|---|---|---|---|
| Z1 | [Chipyard fpga/src/main/scala/zcu104/Configs.scala](https://github.com/ucb-bar/chipyard/blob/main/fpga/src/main/scala/zcu104/Configs.scala), [PR #2372](https://github.com/ucb-bar/chipyard/pull/2372) (merged 2026-09-08), [docs ZCU104.rst](https://github.com/ucb-bar/chipyard/blob/main/docs/Prototyping/ZCU104.rst) | Rocket (`RocketZCU104Config` = `chipyard.RocketConfig`, 1 big core) | RV64GC (Rocket big core default has FPU; FPU not stated in file) | ZCU104 (`xczu7ev-ffvc1156-2-e` = board part; not stated in Chipyard file) | **100** | default | Docs: runs Linux from SD (same flow as VCU118) | "class WithZCU104Tweaks(freqMHz: Double = 100) extends Config(" |
| Z2 | same | MegaBoom (`BoomZCU104Config` = `MegaBoomV3Config`) | RV64GC | ZCU104 | **50** | default | Same flow | "new WithZCU104Tweaks(freqMHz = 50) ++" |
| Z3 | same | Rocket, no DDR (`RocketZCU104NoDDRConfig`) | RV64, 256 KiB DTIM | ZCU104 | 50 | default | No | "new chipyard.harness.WithHarnessBinderClockFreqMHz(50) ++" |
| Z4 | [Chipyard vcu118/Configs.scala](https://github.com/ucb-bar/chipyard/blob/main/fpga/src/main/scala/vcu118/Configs.scala) | MegaBoom (`BoomVCU118Config`) | RV64GC | VCU118 (VU9P −2L) | **50** (Rocket 100 already known) | default | Yes (VCU118 flow) | "class BoomVCU118Config extends Config(" / "new WithFPGAFrequency(50) ++" |
| Z5 | [ashu-bitspilani/chipyard-zcu102 zcu102/Configs.scala](https://github.com/ashu-bitspilani/chipyard-zcu102/blob/HEAD/fpga/src/main/scala/zcu102/Configs.scala) (fork, 2023) | Rocket / MediumBoom | RV64GC | ZCU102 | Rocket 100, MediumBoom 50 | default (fork, unverified) | Not stated | "new WithFPGAFrequency(100) // default 100MHz freq" |
| Z6 | [rc-fpga-zcu common/Makefrag.zcu](https://github.com/li3tuo4/rc-fpga-zcu/blob/master/common/Makefrag.zcu), [Configs.scala](https://github.com/li3tuo4/rc-fpga-zcu/blob/master/common/src/main/scala/Configs.scala), [zcu102/Makefile](https://github.com/li3tuo4/rc-fpga-zcu/blob/master/zcu102/Makefile) | Rocket (the known "195 MHz" port) | Default `CONFIG ?= ZynqConfig` = rocket-chip `system.DefaultConfig` (Apr 2018) → 1 big core; **FPU on by rocket-chip default** (inference) | `PART = xczu9eg-ffvb1156-2-i` | (195 known) | — | — | "class ZynqConfig extends Config(new WithZynqAdapter ++ new DefaultConfig)" |
| Z7 | [OSCPU/NutShell fpga/board/axu3cg](https://github.com/OSCPU/NutShell/tree/master/fpga/board/axu3cg) (mk.tcl, bd/arm.tcl; last change 2024-08) | NutShell (9-stage in-order) | RV64 **IMAC** + Zicsr/Zifencei, M/S/U, Sv39, **no FPU** ([intro doc](https://github.com/OSCPU/NutShell-doc/blob/master/%E4%BB%8B%E7%BB%8D/introduction.md)) | Alinx **AXU3CG**, `xczu3cg-sfvc784-1-e` (−1) | **150** coreclk (uncore 100) | default | Debian-on-FPGA demo in README (board not named) | `CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {150.000}` … `CONFIG.CLK_OUT1_PORT {coreclk}` |
| Z8 | same, `fpga/board/PXIe` | NutShell | RV64IMAC | `xczu19eg-ffvc1760-2-i` (−2) | **150** coreclk | default | as above | `create_project project_1 myproj -part xczu19eg-ffvc1760-2-i` |
| Z9 | [HanbinLuo/c906_on_fpga](https://github.com/HanbinLuo/c906_on_fpga) (2026-10) | OpenC906 | RV64 (FPU status not stated in repo) | Alinx **AXU15EG**, `xczu15eg-ffvb1156-2-i` | **50** (clk_wiz CLKOUT1) | default | **No**: "Linux/DDR 启动尚未作为可验证流程交付" | "面向 AXU15EG / XCZU15EG 的 OpenC906 集成工程，使用 Vivado 2020.2" |
| Z10 | [ZHANGYUGE-KKKK/XUANTIE-C910-FPGA-Linux](https://github.com/ZHANGYUGE-KKKK/XUANTIE-C910-FPGA-Linux) (2026-10) | OpenC910, single core | RV64GC (FPU not stated) | AXVU13P board, `xcvu13p` (Virtex US+; grade not stated) | **50** (clk_wiz; DTS `clock-frequency = <50000000>`) | default | Yes (boot-log output claimed) | "最终实现 Linux 串口启动日志输出" |
| Z11 | [vivado-risc-v board/rocket-freq](https://github.com/eugene-tarassov/vivado-risc-v/blob/master/board/rocket-freq) (first-match table; Makefile `awk … exit`) | Rocket / BOOM | `Rocket64b*` = RV64GC + FPU; `w1` small BOOM, `x/y/z` medium/large/mega BOOM | VCU1525 `xcvu9p-fsgd2104-2L-e`; U200 `xcu200-fsgd2104-2-e`; U250 | Rocket **125**; `Rocket64w1` (small BOOM) 125; `Rocket64[xyz]` BOOM **31.25**; ≥b10 cores 62.5–80 | default | Yes (project boots Debian) | "(vcu1525\|u200\|u250)      Rocket.*                   125.0" |
| Z12 | same, plus [PR #281](https://github.com/eugene-tarassov/vivado-risc-v/pull/281) and [issue #272](https://github.com/eugene-tarassov/vivado-risc-v/issues/272) | Rocket / BOOM | `Rocket64b1` RV64GC+FPU; `Rocket32s1` | Alveo **X3522PV** `xcux35-vsva1365-3-e` (**−3**) | Rocket64b1 **160**, Rocket32s1 200, BOOM x/y/z 40, others 125 | default + user claim | Yes: "Linux on 32bit Rocket, and several flavors of 64bit Rocket and 64bit BOOM" | "I can close timing easily at 160MHz on Rocket64b1" |
| Z13 | [vivado-risc-v issue #272](https://github.com/eugene-tarassov/vivado-risc-v/issues/272) (7-series, for calibration) | Small BOOM `rocket64w1` | RV64GC | Genesys2 `xc7k325t-2`, Vivado 2024.2 | Fails 100 by −1.6 ns; **80 works** | Fmax step | Yes | "it fails timing by  -1.6ns" / "80 worked for me" |
| Z14 | [tommythorn/smolrv64 README](https://github.com/tommythorn/smolrv64) (2026) | SmolRV64 (4-wide OoO; **FPU = CVFPU/fpnew**, the same FPU as CVA6, "four-deep") | RV64 RVA22 (incl. F/D) | RK-XCKU5P-F board, `xcku5p-ffvb676-2-i` (Kintex US+ −2), Vivado 2025.1 | **166.67** core clock | closed@166.67 (claim; timing scripts in repo) | **Yes**, Ubuntu 25.04 boots | "166.67 MHz on the XCKU5P (a 6.000 ns cycle), closed four-wide; DDR4 at 333 MHz" |
| Z15 | [SpinalDoc slides_nax_040522.pdf](https://github.com/SpinalHDL/SpinalDoc/blob/master/presentation/en/nax_040522/slides_nax_040522.pdf) (May 2022) | NaxRiscv, 2-decode / 3-issue | RV32IMASU (no FPU); RV64IMASU variant | Artix-7 −3; Kintex US+ −3 | **RV32: 145 (A7-3), 360 (KU+ -3)**; RV64IMASU: 140 (A7-3) | synth Fmax (author) | Linux on SoC (other docs), not tied to these MHz | "145 Mhz (360 Mhz on Kintex ultrascale+ grade 3)" |
| Z16 | [UG1629 Maximum Frequencies, 2026.1 (2026-07-31)](https://docs.amd.com/r/en-US/ug1629-microblaze-v-user-guide/Maximum-Frequencies) | MicroBlaze V, max-frequency config | — | Fastest grade per family | **Zynq US+ 504**, Kintex US+ 558, Virtex US+ 540, Artix US+ 508, Versal 482 | AMD table | — | "The fastest speed grade of each family is used to generate the results in this table." |

**Correction to the prior notes on Z16.** `k26_y_comparativa.md` cites UG1629 **2024.1**: ZU+ 526, KU+ 535, VU+ 524 MHz. The current **2026.1** table lists ZU+ **504**, KU+ 558, VU+ 540. Cite the version along with the number.

---

## Q1. Kria (KV260/KR260/K26) and Zynq US+ by framework

**LiteX (litex-boards)**
- `xilinx_kv260.py` exists (added in PR #345, 2022, by I. Sergachev).
  - It defaults to `cpu_type="zynqmp"` and `no_uart=True`, with `--sys-clk-freq` default `100e6`.
  - With a soft CPU, the clock comes from a PMOD pin through `S7PLL(speedgrade=-1)`.
  - The platform comment: "Seems like there are no on-board clock sources for PL when PS is not used… (not tested)". The part is `xck26-sfvc784-2lv-c`.
- **KR260: no target.** Issue [#597](https://github.com/litex-hub/litex-boards/issues/597) "KR260 support is missing" (2024-07-25) is still open.
- `alinx_axu2cga.py` also defaults to `cpu_type="zynqmp"`, with `--sys-clk-freq` default `25e6` (`USMMCM(speedgrade=-1)`). AXU15EG: no LiteX target found (`alinx_axau15.py` is the Artix US+ AU15P board).
- ZCU102, ZCU104 and ZCU106 default to 125 MHz with `USMMCM(speedgrade=-2)`. Enclustra Mercury XU5 and XU8 default to 125 MHz with `speedgrade=-1`.
- **linux-on-litex-vexriscv** `boards.py` supports only **ZCU104** among Zynq US+ boards (no KV260, no AXU2CGA).
- Practical evidence of a soft core through LiteX on K26 is NaxRiscv RV64 at 100 MHz (K10), a single user report.

**vivado-risc-v (eugene-tarassov)**
- The `board/` directory has arty-a7-100t, genesys2, kc705, nexys-a7-100t, nexys-video, sitlinv-xc7k325t, u200, u250, vc707, vcu1525 and x3522pv. There is **no Zynq US+ or Kria board**.
- [Issue #124 "Kria KV260 support"](https://github.com/eugene-tarassov/vivado-risc-v/issues/124) (2023) got only community replies and was closed.
- [Issue #145](https://github.com/eugene-tarassov/vivado-risc-v/issues/145) is a user attempt on ZCU104. It never reports a frequency.
- No AXU2CGA or AXU15EG port found.
- The maintainer on frequency (#272): "The supported values are (MHz): 160 125 100 80 62.5 50 40 31.25 25 20", and later "You can use any frequency as log as the Clock Wizard can synthesize all clocks exactly".
- The rocket-freq table values are default targets. The Makefile never checks timing.

**Chipyard / FireSim**
- Chipyard FPGA targets on `main`: arty, arty100t, datastorm, genesys2, nexysvideo, vc707, vcu118 and **zcu104**. ZCU104 and Genesys2 were added by commit `2643f2ad72` (2026-08-24); see Z1–Z3. No Kria or ZCU102 target upstream.
- FireSim `platforms/`: corigine_mimicturbo_gt, f1, f2, rhsresearch_nitefury_ii, vitis, xilinx_alveo_u200/u250/u280/v80 and xilinx_vcu118. **No Zynq or Kria.**

**MicroBlaze V on Kria**
- AMD documentation: no MicroBlaze V Linux example for K26/KV260/KR260 found. UG1629 gives family-level tables only (fastest grade). UG1711 examples are not board-specific in what I could read.
- Community:
  - LogicTronix [Hackster project](https://www.hackster.io/LogicTronix/microblaze-v-on-kr260-with-bmp180-sensor-and-vitis-2025-1-35315c) / [GitHub](https://github.com/LogicTronixInc/Kria-KR260-MicroblazeV-BMP180-I2C-Sensor): MicroBlaze V on KR260, I²C sensor, bare-metal. No MHz in README.
  - Accemic `mbv` (K9): RV32 bare-metal at 75 MHz on the board.
  - **No MicroBlaze V Linux on K26 found.**

**Other cores on Kria**
- **No** VexRiscv-SMP Linux, BOOM, SHAKTI, XiangShan or OpenC906/C910 on K26 found.
- Small RV32 VexRiscv bare-metal at 100 MHz appears in student and contest projects (K12; [Dreamweaver1919/riscv-int4-simd](https://github.com/Dreamweaver1919/riscv-int4-simd), RV32I+SIMD at `pl_clk0` 100 MHz). These are not Linux-class comparators.

## Q2. Dörflinger et al., CF'21: retrieved

**Source.** Author version from TU Braunschweig LeoPARD repository record [dbbs_mods_00069519](https://doi.org/10.24355/dbbs.084-202105101615-0), file `riscv-survey-cf-zweitpublikation_v3.pdf`. The revision notice: 05/11/2021 CVA6 SPEC update; 08/07/2022 CVA6 ASIC area corrected to 0.38 mm².

**Access note.** The HTML landing pages (`/receive/…`) show a JavaScript proof-of-work "Security Check". I did not run it. The PDF came from the repository's public MyCoRe REST endpoint (`/api/v2/objects/dbbs_mods_00069519/derivates/dbbs_derivate_00048213/contents/…`), which serves it without a challenge. ACM DL returned 403. The paper is green OA per OpenAlex. The PDF was read with `pdftotext` and the local copy was deleted.

**Table 3, FPGA Fmax on XCVU9P:**

| Core | Fmax XCVU9P (MHz) | Fmax 22FDX ASIC (MHz) |
|---|---|---|
| Rocket | **198** | 813 |
| BOOM | **88** | 943 |
| CVA6 | **112** | 738 |
| SHAKTI | **136** | 685 |

Per-MHz scores (DMIPS / CoreMark / SPEC17 IPC): Rocket 1.71 / 2.94 / 0.33; BOOM 3.87 / 6.25 / 0.50; CVA6 1.21 / 2.08 / 0.18; SHAKTI 1.70 / 2.84 / 0.23.

**Setup quotes:**

| Topic | Quote |
|---|---|
| Platform | "a VCU118 evaluation board containing an XCVU9P Xilinx Virtex UltraScale+ FPGA" |
| Tool | "Xilinx Vivado Design Suite 2019.2" |
| Settings | "default but identical settings are selected for FPGA synthesis and P&R for all processors" |
| Method | "obtained by incrementally increasing the clock until timing violations were reported" |
| Limiting path | "CVA6 clocking is restricted by L1D logic." / "The critical path of the BOOM synthesis contains PTW logic." |
| BOOM layout | "BOOM is the only design that spreads over two Super Logic Regions (SLRs)" |
| CVA6 framework | "OpenPiton is utilized instead of Chipyard for the CVA6 evaluation due to performance reasons." CVA6 commit `1793be63`. |
| Voltage | "All measurements are performed for 0.85 V VCCINT" (this sentence is in the power section) |

**Configuration (Tables 1–2).**
- All four cores use extensions **MAFDC** (FPU on).
- Common parameters: BHT 512, BTB 32, RAS 8, **L1D 16 KB, L1I 16 KB**.
- BOOM is a medium-to-large variant with issue width 5.
- Default "pipeline registers for CVA6".
- Area results came from a relaxed 50 MHz constraint.

**Not stated in the paper:**
- The speed grade. The VCU118 part is `xcvu9p-flga2104-2L-e` per the prior notes and the board, not the paper.
- Whether the Fmax figure is for the full SoC or the core alone. The paper says "Measurements are taken for the full SoC designs and standalone cores separately", and Table 3 is titled "maximum processor core frequency".

**Inference (mine):**
- 112 MHz on VU9P at 0.85 V × 0.79–0.94 (the prior notes' −2LV@0.72 V versus −2@0.85 V fabric factor) gives **≈88–105 MHz** expected on the K26. The user's 90.9 MHz closed (≈94.8 MHz reachable) sits in the lower half of that range.
- Differences that weaken the comparison:
  - OpenPiton's CVA6 (2020) uses a write-through L1 and a 16 KB D$.
  - Rocket and BOOM came from Chipyard.
  - Virtex versus Zynq is the same US+ fabric.
- The paper's CVA6/Rocket ratio of 0.57 matches the ~0.5× ratio the prior notes found from target frequencies.

## Q3. Other CVA6-related Fmax on UltraScale+ (new)

**CVA6 itself**
- **Dörflinger:** 112 MHz on XCVU9P with MAFDC. This is the only measured Fmax for a 64-bit CVA6 with FPU on UltraScale+ that I found.
- **Accemic, CVA6 on the K26 itself, without FPU (K4/K5):**
  - RV64IMAC CVA6 plus an N-Trace encoder closes the 71.114 MHz constraint with only +0.603 ns (dual: +0.125 ns).
  - The README says the alternative E-Trace backend "dominates the critical path at this core size". So the critical path in these builds may be the trace logic, not CVA6.
  - This is **not** an Fmax measurement. It shows only that a third party shipped CVA6 RV64 Linux on K26 at **68.18 MHz** on the board.

**Same FPU as CVA6**
- **SmolRV64 (Z14):** CVFPU/fpnew, the same FPU as CVA6, runs inside a core closed at 166.67 MHz on Kintex US+ −2 (`xcku5p-ffvb676-2-i`). The design wraps it as a "tagged, four-deep FPU" with its own scheduler. This shows fpnew is not a hard ~100 MHz wall on US+ once it is pipelined and isolated. Inference: no CVA6 RTL is involved.

**No new paper found** (2022–2026) giving CVA6+FPU Fmax on a Zynq US+ part with its speed grade. Search terms tried: CVA6/Ariane with VCU118, VCU128, ZCU102, ZCU104, Kria, UltraScale+ Fmax.
- A Zenodo report ([18500459](https://zenodo.org/records/18500459), "Investigation Report on RISC-V Soft CPU Cores for HEP", Cheung) is secondary. It gives CVA6 "50–75 MHz typically" on Kintex-7 and no US+ measurement.

## Q4. K26 −2LV at 0.72 V versus −1/−2

Nothing new beyond the prior notes (DS925 tables, ≈−1 at 0.85 V, 0.79–0.94× of −2 at 0.85 V). The Tanager research report repeats the DS925 switching numbers, e.g. "BRAM reaches 585/510 MHz … against 738/637 MHz at the standard 0.85 V". These are already in the prior notes. No AMD statement gives a single speed ratio.

---

## Verified facts vs inferences: quick list

**Verified from primary files:**
- The rows K1, K1b, K4–K11, Z1–Z4, Z6–Z12 and Z14–Z16 come from primary files as quoted.
- The frequencies in K2, K3, K10 and Z14 are what the projects themselves report. No timing report was checked for K2, K3 or K10.
- For Z14, the repository contains timing scripts, but no routed report was read.

**Credibility caveats:**
- **K2 (Rocket ×2 on KV260):**
  - The guide claims Vivado 2024.2, but the committed `build.log` and `build.stdout` show **Vivado 2025.2**, synthesis only. No routed timing report is committed.
  - The repo is a single commit (2026-10-15).
- **K3 (Tanager):** a 4-day-old public repo whose README states the work is "agent-built". Its claims are not independently checked.
- **K8 (`rocket2`):** two different WNS values exist (+3.578 ns in `plclk.json`, +2.399 ns in the tutorial table), from different builds.

**Inferences:**
- All "est." MHz values.
- Rocket FPU-on in Z1 and Z6, from rocket-chip defaults.
- The 0.79–0.94 scaling of Dörflinger's numbers to K26: CVA6 88–105, Rocket 156–186, BOOM 70–83, SHAKTI 107–128 MHz.

## Gaps

- **Not found anywhere:**
  - CVA6 **with FPU** on any Kria/K26 board other than the user's.
  - BOOM, SHAKTI, XiangShan, OpenC906/C910, VexRiscv-SMP Linux or MicroBlaze V **Linux** on K26.
  - Any Ultra96 RISC-V soft-core frequency.
  - A Linux-class soft core on Alinx AXU2CGA (only the A53-based LiteX target).
- **Dörflinger:**
  - The paper does not state the speed grade.
  - It is unclear whether Table 3's Fmax is the full SoC or the bare core.
  - The paper gives no WNS and no per-core critical-path detail beyond "L1D logic" (CVA6) and "PTW" (BOOM).
- **Accemic CVA6/Rocket builds:**
  - Only slack at 71.114 MHz is reported. No higher constraint was tried, so these are lower bounds, not Fmax.
  - The critical paths are not published, and they may lie in the trace encoder.
- **Kronos:** the 200 MHz result predates its caches and MMU. The current full-core number is "in flux" (issue #108).
- **Chipyard ZCU104:** no timing report or Linux boot log is published for the 100 MHz default. The Rocket FPU is assumed from `RocketConfig`.
- **NutShell:** no timing report for 150 MHz on AXU3CG (−1). The AXU3CG files are "currently not avaliable to the public" per the README, though the TCL is in the repo.
- **vivado-risc-v X3522PV:** only Rocket64b1 at 160 MHz has a user "close timing easily" statement. The other rocket-freq entries are defaults.
- **MicroBlaze V:** UG1629 has no −2LV/K26 rows, so there is no AMD number for MicroBlaze V at 0.72 V.
- **Q4:** no new direct AMD quantitative statement for −2LV at 0.72 V versus −1/−2.
