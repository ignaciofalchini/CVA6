# CVA6/Ariane clock frequencies on FPGAs: papers, PULP/Princeton/Columbia SoCs, and third-party ports (UltraScale/UltraScale+ emphasis)

Research date: 2026-10-27. Method: web search/fetch of papers and project pages, plus shallow clones of the repositories (HEAD as of the date shown per row), grepping XDC/Tcl/IP (.xci)/Makefile/DTS files for clock settings. **"Target" means the value is a constraint or clock-generator setting in a shipped flow. "Reported" means a paper or post states the design ran at that frequency. None of the repositories ship a timing report, so "target" does not prove timing was met.** Unless noted otherwise, the clock is the CVA6 core's clock domain.

User baseline, for comparison only: unmodified `cv64a6_imafdc_sv39` on a KR260 (K26, `xck26-sfvc784-2LV-c`), Vivado 2026.1. It meets timing at 90.9 MHz and fails at 100 MHz with WNS −0.553 ns.

---

## Q0. Master table of reported CVA6/Ariane FPGA implementations

### Takeaway
Across 30+ data points, shipped flows on UltraScale/UltraScale+ run CVA6 at **25–78 MHz** in most cases, and 50 MHz is by far the most common setting. **100 MHz** appears only in Princeton's OpenPiton/BYOC ecosystem (VCU118 system clock, and the SMAPPIC paper on AWS F1 VU9P). There it is the whole-system clock of an OpenPiton tile (write-through L1 plus L1.5), the FPU status is not stated in the paper, and no timing report is published. The best single "64-bit, FPU on, US+" calibration point is a 2026 VU33P PCIe port. It defaults `cv64a6_imafdc_sv39` to 50 MHz and states that "Heavy configs can't close at 100 MHz", even with synthesis retiming and FPnew KEEP attributes removed.

### Cited Findings

#### A. UltraScale / UltraScale+ / Versal implementations

| # | Project / source (date) | Board, device (family, speed grade) | CVA6 config | CVA6 clock | Status | Source |
|---|---|---|---|---|---|---|
| 1 | OpenPiton (+Ariane via `--core=ariane`) `system` design, VCU118 (repo HEAD Feb 2026) | VCU118, `xcvu9p-flga2104-2L-e` (Virtex US+, -2L) | Ariane/CVA6 in an OpenPiton tile (write-through L1 + L1.5). The pinned CVA6 commit `4c01614` enables F/D for 64-bit under `PITON_ARIANE`; the config package is `cv64a6_imafdc_sv39_openpiton` with `CVA6ConfigFpuEn = 1`. The OpenPiton README still says "RV64IMAC" (historical). | **100 MHz** (block.list `vcu118,100`; `clk_mmcm.xci` CLKOUT1 = 100) | Target. Timing not stated. | [block.list](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/piton/tools/src/proto/block.list), [vcu118 clk_mmcm.xci](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/piton/design/chipset/xilinx/vcu118/ip_cores/clk_mmcm/clk_mmcm.xci), [ariane_pkg @4c01614](https://github.com/openhwgroup/cva6/blob/4c01614f83cd9dd91d115aa190bd4fc6a284b59e/core/include/ariane_pkg.sv), [README](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/README.md) |
| 2 | OpenPiton `system`, BittWare XUPP3R | `xcvu9p-flgb2104-2-e` (Virtex US+, -2) | same as #1 | **60 MHz** | Target | [block.list](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/piton/tools/src/proto/block.list) |
| 3 | OpenPiton+Ariane on AWS EC2 F1 (`piton_aws`), OpenPiton release 13 (2019) | AWS F1, `xcvu9p-flgb2104-2-i` (Virtex US+, -2) | same as #1 | **62.5 MHz** | Target | [block.list](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/piton/tools/src/proto/block.list), [F1 blog](https://openpiton-blog.princeton.edu/2019/10/bringing-openpiton-to-amazon-ec2-f1-fpgas) |
| 4 | SMAPPIC, Chirkov & Wentzlaff, ASPLOS'23 | AWS F1 (VU9P) | Ariane, RV64, 6-stage in-order, Linux 5.12. L1I 16 KB, L1D 8 KB, 16 ITLB / 16 DTLB entries. **FPU not stated.** | **100 MHz** for configs 1x10, 2x4, 4x2. **75 MHz** for 1x12 (97% LUTs) and 2x5 (88% LUTs). | Reported prototype frequencies | [SMAPPIC PDF](https://par.nsf.gov/servlets/purl/10470689) (Table 2, Table 4) |
| 5 | OpenPiton+Ariane slides, ETH RISC-V workshop (2019) | VCU118 / BittWare XUPP3R | OpenPiton+Ariane | ">100MHz" | **Expectation** ("In progress") | [opariane-wosh.pdf](https://pulp-platform.org/docs/riscv_workshop_zurich/opariane-wosh.pdf), slide 21 |
| 6 | ESP (Columbia), Ariane CPU tile, VCU118 (repo Sep 2026) | `xcvu9p` (VCU118, -2L) | ESP's Ariane fork (`sld-columbia/ariane` @21ee234): `RVF = 1`, `RVD = 1` (RV64GC with FPU), Linux-capable, Sv39 | Tiles' `refclk` = MIG `ADDN_UI_CLKOUT1_FREQ_HZ {78}`, so **~78 MHz** (78.125 MHz in the simulation model). Memory tiles run on MIG `ui_clk` (~156 MHz). | Target | [mig.tcl](https://github.com/sld-columbia/esp/blob/main/constraints/xilinx-vcu118-xcvu9p/ariane/mig.tcl), [top.vhd](https://github.com/sld-columbia/esp/blob/main/socs/xilinx-vcu118-xcvu9p/top.vhd), [ariane_pkg @21ee234](https://github.com/sld-columbia/ariane/blob/21ee2341cd91637ffe2039cfa17a5790c02c4cdb/include/ariane_pkg.sv) |
| 7 | ESP, VCU128 | `xcvu37p` (Virtex US+ HBM, -2L) | same as #6 | **75 MHz** (`ADDN_UI_CLKOUT1_FREQ_HZ {75}`) | Target | [mig.tcl](https://github.com/sld-columbia/esp/blob/main/constraints/xilinx-vcu128-xcvu37p/ariane/mig.tcl) |
| 8 | ESP, proFPGA VU440 / proFPGA VU19P | `xcvu440` (Virtex UltraScale) / `xcvu19p` (Virtex US+) | same as #6 | **78 MHz** (both) | Target | [constraints dir](https://github.com/sld-columbia/esp/tree/main/constraints) (`profpga-xcvu440/ariane/mig.tcl`, `profpga-xcvu19p/ariane/mig.tcl`) |
| 9 | ESP, ZCU102 / ZCU106 | `xczu9eg` / `xczu7ev` (Zynq US+) | ESP SoC. Whether the Ariane tile is used on these boards was not verified. | PL clock `pl_clk0` = **75 MHz**, wired to `chip_refclk` | Target | [zcu102 zynq.tcl](https://github.com/sld-columbia/esp/blob/main/constraints/xilinx-zcu102-xczu9eg/zynq.tcl), [zcu106 zynq.tcl](https://github.com/sld-columbia/esp/blob/main/constraints/xilinx-zcu106-xczu7ev/zynq.tcl) |
| 10 | Cheshire (PULP), VCU118 and VCU128 (repo Oct 2026) | `xcvu9p-flga2104-2L-e`, `xcvu37p-fsvh2892-2L-e` | `cv64a6_imafdchsclic_sv39_wb` (RV64GC + H + CLIC, Sv39, write-back D$) | **50 MHz** (`clk_wiz` CLKOUT1 = 50; `SOC_TCK 20.0`) | Target | [impl_ip.tcl](https://github.com/pulp-platform/cheshire/blob/main/target/xilinx/scripts/impl_ip.tcl), [vcu118.xdc](https://github.com/pulp-platform/cheshire/blob/main/target/xilinx/constraints/vcu118.xdc), [vcu128.xdc](https://github.com/pulp-platform/cheshire/blob/main/target/xilinx/constraints/vcu128.xdc), [cheshire.mk](https://github.com/pulp-platform/cheshire/blob/main/cheshire.mk) |
| 11 | Carfield (PULP), VCU128 (default) and VCU118 (repo May 2026) | `xcvu37p-fsvh2892-2L-e`, `xcvu9p-flga2104-2L-e` | Cheshire host (dual CVA6 with H extension) | Host domain **50 MHz** (`SOC_TCK 20`, `clk_50`). The flow comments "Runtime optimized due to the low frequency (50/20MHz)". | Target | [carfield.xdc](https://github.com/pulp-platform/carfield/blob/main/target/xilinx/constraints/carfield.xdc), [xilinx.mk](https://github.com/pulp-platform/carfield/blob/main/target/xilinx/xilinx.mk), [flavor_vanilla run.tcl](https://github.com/pulp-platform/carfield/blob/main/target/xilinx/flavor_vanilla/scripts/run.tcl) |
| 12 | Ara (+Cheshire), VCU128 and VCU118 (repo Aug 2026) | as #10 | CVA6 + Ara vector unit (2 lanes tested) | **50 MHz** (device-tree patch `clock-frequency = <50000000>; // 50 MHz`) | Target | [Ara README](https://github.com/pulp-platform/ara/blob/main/README.md), [device_tree.patch](https://github.com/pulp-platform/ara/blob/main/cheshire/patches/device_tree.patch) |
| 13 | Occamy (PULP), VCU128 (repo Sep 2024) | VCU128 (`xcvu37p`) | CVA6 host, DTS `rv64fimafd`, `riscv,sv39` (FPU on) | **25 MHz** (DTS CPU `clock-frequency = <25000000>`; `clk_wiz` outputs 100/25/12.5/120 MHz) | Target | [occamy.dts](https://github.com/pulp-platform/occamy/blob/main/target/fpga/bootrom/occamy.dts), [occamy_vcu128_bd.tcl](https://github.com/pulp-platform/occamy/blob/main/target/fpga/occamy_vcu128_bd.tcl) |
| 14 | HeMAiA (KU Leuven MICAS, Occamy-derived), VCU128 (repo Sep 2026) | VCU128 (`xcvu37p`). A Versal VPK180 (`xcvp1802-lsvc4072-2MP-e`) target also exists. | CVA6 host + SNAX clusters (CVA6 config not checked) | `clk_main` 250 MHz ÷ 6 = **~41.7 MHz** (`clk_core`) on VCU128. VPK180 core clock not determined. | Target | [hemaia_system_vcu128_impl.xdc](https://github.com/KULeuven-MICAS/HeMAiA/blob/main/target/fpga/hemaia_system/hemaia_system_vcu128_impl.xdc) |
| 15 | cva6_fk33 (aebarthyi, Jun 2026): CVA6 over PCIe XDMA | SQRL Forest Kitten 33, `xcvu33p-fsvh2104-2-e` (Virtex US+ HBM, -2) | `cv64a6_imafdc_sv39` (default `TARGET_CFG`) | **50 MHz** default for imafdc. 100 MHz for the other (lighter) configs. | Target. The author notes the heavy configs fail at 100 MHz (see Q6). | [Makefile](https://github.com/aebarthyi/cva6_fk33/blob/main/Makefile), [pre_opt_design.tcl](https://github.com/aebarthyi/cva6_fk33/blob/main/vivado/pre_opt_design.tcl) |
| 16 | FleXNNgine-CVA6 (Sep 2026) | VCU118, `xcvu9p-flga2104-2L-e` | `cv64a6_imafdch_sv39_wb` | **50 MHz** ("CVA6 + AXI + PE array"); accelerator scratchpad at 250 MHz | Target | [clock_uplift.xdc](https://github.com/FoivosParaskevas/FleXNNgine-CVA6/blob/main/fpga/scripts/clock_uplift.xdc), [fpga/Makefile](https://github.com/FoivosParaskevas/FleXNNgine-CVA6/blob/main/fpga/Makefile) |
| 17 | jctullos/cva6 VCU118 port (2020, referenced in CVA6 issues #516/#2413) | `xcvu9p-flga2104-2L-e` | Upstream CVA6 APU of 2020 (64-bit; FPU default not verified) | **50 MHz** (`CLK_PERIOD_NS := 20`) | Target | [commit 7c290d1](https://github.com/jctullos/cva6/commit/7c290d1b22cd57645555440f88dbba1295b46ed5), [issue #516](https://github.com/openhwfoundation/cva6/issues/516) |
| 18 | Upstream CVA6 `vcu118.xdc` (since 2021-09 re-org) | VCU118 | n/a | No CVA6 frequency set. The top Makefile has no `vcu118` BOARD entry; the XDC only defines a 100 MHz `sys_clk` input. | Incomplete flow | [vcu118.xdc](https://github.com/openhwgroup/cva6/blob/master/corev_apu/fpga/constraints/vcu118.xdc), [Makefile](https://github.com/openhwgroup/cva6/blob/master/Makefile) |
| 19 | Cuomo et al., "Towards a RISC-V Open Platform for Next-generation Automotive ECUs" (arXiv 2307.04148, 2023) | ZCU102 (`xczu9eg`) PL | CVA6 RV64GC (G+C) with MMU/TLB, real-time-enhanced (modified RTL) | **50 MHz** ("synthesized on the PL targeting 50 MHz") | Target | [arXiv 2307.04148](https://arxiv.org/abs/2307.04148) |
| 20 | SoC-all-core (thanhtruong332, Oct 2026) | ZCU102, `xczu9eg-ffvb1156-2-e` | `cv32a6_imac_sv0` (32-bit, no FPU, no MMU) | **40 MHz** default (`clk_wiz` CLKOUT1 = 40). The README explains how to measure fmax but reports none. | Target | [README](https://github.com/thanhtruong332/SoC-all-core/blob/main/README.md), [cva6_soc create_project.tcl](https://github.com/thanhtruong332/SoC-all-core/blob/main/socs/cva6_soc/create_project.tcl) |
| 21 | corejack (patrickerich, Oct 2026) | Alinx AXKU5 (Kintex US+ KU5P) | CVA6 (config not found) | **25 MHz** (Zephyr DTS `clock-frequency = <25000000>`) | Target, low confidence | [corejack_cva6_axku5.dts](https://github.com/patrickerich/corejack/blob/main/sw/zephyr/boards/corejack/corejack_cva6_axku5/corejack_cva6_axku5.dts) |
| 22 | CHORYS (FriedDede, Jan 2026) | Alveo U55C, `xcu55c-fsvh2892-2L-e` | CVA6 (config not found) | **50 MHz** (`clk_wiz` comment in `u55_cva6_sim.sv`) | Target in a file named "sim". Low confidence. | [u55_cva6_sim.sv](https://github.com/FriedDede/CHORYS_RISCV-V/blob/master/hw/tops/u55_cva6_sim.sv) |
| 23 | Chipyard `CVA6Config` on VCU118 (CVA6 issue #580, 2021) | VCU118 (VU9P) | Chipyard CVA6 (default Chipyard CVA6 config) | Not stated. Users composed `WithVCU118Tweaks` (default `WithFPGAFrequency(100)`) with `CVA6Config`, so 100 MHz would be the default bus clock if not overridden (inference). | Unverified | [issue #580](https://github.com/openhwfoundation/cva6/issues/580), [Chipyard vcu118 Configs.scala](https://github.com/ucb-bar/chipyard/blob/main/fpga/src/main/scala/vcu118/Configs.scala) |
| 24 | CVA6 issue #338 (2019): Ariane ported to VCU108 | VCU108 (Virtex UltraScale `xcvu095`) | Ariane 2019 | Not stated ("I have not tried to increase the clock speed") | n/a | [issue #338](https://github.com/openhwfoundation/cva6/issues/338) |
| 25 | Kria KR260 "multicore-on-fpga" (turing-house-community, Oct 2026) | KR260 | `cv64a6_imafdc_sv39` + custom instructions | None. "FPGA bring-up on the Kria KR260" is listed under "What's next". | Not done | [README](https://github.com/turing-house-community/multicore-on-fpga/blob/main/README.md) |

#### B. 7-series and other parts, for comparison

| # | Project / source (date) | Board, device | CVA6 config | CVA6 clock | Status | Source |
|---|---|---|---|---|---|---|
| 26 | Upstream CVA6/APU flow (repo HEAD 2026-10-23, master now read-only) | Genesys2 `xc7k325tffg900-2`; KC705 `xc7k325tffg900-2`; VC707 `xc7vx485tffg1761-2` | default `cv64a6_imafdc_sv39` | **50 MHz** (`CLK_PERIOD_NS := 20`; `xlnx_clk_gen` CLKOUT1 = 50) | Target | [Makefile](https://github.com/openhwgroup/cva6/blob/master/Makefile), [xlnx_clk_gen run.tcl](https://github.com/openhwgroup/cva6/blob/master/corev_apu/fpga/xilinx/xlnx_clk_gen/tcl/run.tcl) |
| 27 | Upstream CVA6, Nexys Video | `xc7a200tsbg484-1` (Artix-7) | (32-bit flow) | **25 MHz** (`CLK_PERIOD_NS := 40`; CLKOUT1 = 25) | Target | same as #26 |
| 28 | Ariane v4.1.0 CHANGELOG (release adding "Official support for floating point unit", ~2018–19) | Genesys2 | Ariane with FPU | **30 MHz** ("Reduce clock frequency of FPGA to 30 MHz to accomodate FPU") | Target | [CHANGELOG.md](https://github.com/openhwgroup/cva6/blob/master/CHANGELOG.md) |
| 29 | CVA6 issue #226 (Apr 2019, ETH maintainer M. Schaffner) | Genesys2 (Kintex-7, -2) | Ariane, standalone and in OpenPiton | **60 MHz** used for Kintex-7 mappings. Before an FPU fix, FPU-enabled builds needed **30 MHz**. "100MHz is a bit too tight, even without FPU." | Reported by maintainer | [issue #226](https://github.com/openhwfoundation/cva6/issues/226) |
| 30 | CVA6 issue #77 (2018, F. Zaruba) | Virtex-7 | early Ariane | ~**50 MHz** ("closing timing at approximately 50 MHz on a Virtex 7") | Reported by author | [issue #77](https://github.com/openhwfoundation/cva6/issues/77) |
| 31 | OpenPiton Genesys2 / VC707 / Nexys Video (release 5, 2017 onward; block.list today) | `xc7k325tffg900-2` / `xc7vx485tffg1761-2` / Artix-7 | OpenPiton system (Ariane option since release 12) | **66.667 / 60 / 30 MHz** | Target. VC707 was lowered to 60 MHz "to better guarantee that implementation meets timing". | [block.list](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/piton/tools/src/proto/block.list), [Release 5 blog](https://openpiton-blog.princeton.edu/2017/06/openpiton-release-5), [slides](https://pulp-platform.org/docs/riscv_workshop_zurich/opariane-wosh.pdf) ("1-2 cores at 66MHz", "1-4 cores at 60MHz", "1 core at 30MHz") |
| 32 | BYOC, Balkind et al., ASPLOS'20 | Genesys2 (`7k325tffg900-2`) | Ariane, built with and without FPU (LUT-breakdown figure) | **66.67 MHz** (Oxy and Dicho prototypes). The paper says BYOC is "realised on FPGA (at ~100MHz)" in general. | Reported | [BYOC PDF](https://par.nsf.gov/servlets/purl/10201514) |
| 33 | Cheshire, Genesys2 | `xc7k325tffg900-2` | `cv64a6_imafdchsclic_sv39_wb` | **50 MHz** | Target | [impl_ip.tcl](https://github.com/pulp-platform/cheshire/blob/main/target/xilinx/scripts/impl_ip.tcl) |
| 34 | Culsans (Tedeschi et al., 2024), Genesys2 | `xc7k325t` | up to 4 coherent `cv64a6_imafdc_sv39(_wb)` cores | **50 MHz** (`xlnx_clk_gen` CLKOUT1 = 50). The paper (arXiv 2407.19895) gives no FPGA frequency. | Target | [culsans clk_gen run.tcl](https://github.com/pulp-platform/culsans/blob/master/fpga/xilinx/xlnx_clk_gen/tcl/run.tcl), [arXiv 2407.19895](https://arxiv.org/abs/2407.19895) |
| 35 | CVA6-H virtualization DSE, Sá et al. (arXiv 2302.02969, 2023) | Genesys2 | CVA6 + H extension, 32 KiB D$ / 16 KiB I$, Linux + Bao, Vivado 2020.2 | **100 MHz** ("targeting the Genesys2 FPGA at 100MHz") | Stated as target. No timing report. Conflicts with rows 29 and 26 (see Q6). | [arXiv 2302.02969](https://arxiv.org/abs/2302.02969) |
| 36 | ESP, VC707 | `xc7vx485t` | ESP Ariane (RV64GC) | **50 MHz** (`clkgen` ×16/÷32 from the 100 MHz MIG `ui_clk` → `chip_refclk`) | Target (inferred from code) | [vc707 top.vhd](https://github.com/sld-columbia/esp/blob/main/socs/xilinx-vc707-xc7vx485t/top.vhd) |
| 37 | Thales CVA6 softcore contest (2025-26 branch) | Zybo Z7-20, `xc7z020clg400-1` | `cv32a6_im_contest` (32-bit) | **40 MHz** (`CLK_PERIOD_NS := 25`) | Target | [contest Makefile](https://github.com/ThalesGroup/cva6-softcore-contest/blob/cv32a6_contest_25_26/Makefile) |

### Inferences
- The modal frequency for 64-bit CVA6 with FPU in maintained PULP/ETH flows is 50 MHz on every board, Kintex-7 and Virtex US+ alike (Cheshire, Carfield, Ara, Culsans, upstream CVA6). These flows were not retuned for UltraScale+, so their 50 MHz says nothing about the speed limit on US+.
- The values actually tuned for UltraScale+ are ESP at 75–78 MHz and OpenPiton/SMAPPIC at 100 MHz (60–62.5 MHz on XUPP3R/F1 in `block.list`). In both projects CVA6 sits in a different memory subsystem from the stock CVA6 APU and Cheshire.
- SMAPPIC's own data shows frequency falling (100 → 75 MHz) as LUT utilization rises toward 88–97%. Routing congestion on a nearly full VU9P therefore affects the achievable clock, not only CVA6's logic depth.

### Gaps
- None of the repositories publish post-route timing reports. For "target" rows, it is not proven that timing was met, though shipped default flows presumably close.
- SMAPPIC's FPU configuration is not stated. OpenPiton's current pinned CVA6 enables F/D, but it is not documented which CVA6 version and FPU setting SMAPPIC used.
- No CVA6 frequency could be determined for the HeMAiA VPK180 (Versal Premium) target, HERO's VCU128 CVA6 host ("under development" per [HERO README](https://github.com/pulp-platform/hero)), the UNIMORE HeSoC repo ([richie-hesoc](https://github.com/Advanced-Architectures-UNIMORE/richie-hesoc), which lists CVA6 as a host option; its ZCU102/ZCU104/Ultra96 PL clocks are 100/50/50 MHz, but it was not verified that CVA6 is clocked by them), or merledu/nova (an Ariane SoC on AWS F1).
- The Dörflinger et al. CF'21 survey ("A comparative survey of open-source application-class RISC-V processor implementations"), which benchmarks Rocket/BOOM/CVA6/SHAKTI on Virtex UltraScale+ with Vivado 2019.2, could not be retrieved: the TU Braunschweig and ACM PDFs are behind bot checks. Its CVA6 FPGA frequency is therefore unknown here and worth obtaining manually ([Lübeck record](https://research.uni-luebeck.de/en/publications/a-comparative-survey-of-open-source-application-class-risc-v-proc/), DOI 10.1145/3457388.3458657).

---

## Q1. Original Ariane paper (Zaruba & Benini, IEEE TVLSI 2019) and related ETH/PULP papers: what FPGA frequency did they report?

### Takeaway
The Ariane TVLSI paper reports no FPGA clock frequency. It only mentions a "ready-to-go FPGA bitstream". Its frequencies are ASIC numbers (up to 1.7 GHz in GF 22FDX). The Cheshire and Culsans papers also give no FPGA frequency. ETH's FPGA numbers come from repositories and maintainer comments: 30 MHz (Ariane with early FPU), then 50–60 MHz on Kintex-7, and 50 MHz in Cheshire, Carfield and Ara today.

### Cited Findings
- The Ariane paper's only FPGA statement is that the authors "provide support for Verilator- and QuestaSim-based RTL simulation as well as a ready-to-go FPGA bitstream and a pre-built Linux image". No board or frequency is given. — [arXiv 1904.05442](https://arxiv.org/abs/1904.05442)
- The same paper's silicon figure: an Ariane instance (RV64IMC) taped out in GF 22FDX "runs at up to 1.7 GHz". — [arXiv 1904.05442](https://arxiv.org/abs/1904.05442)
- The Cheshire paper (Ottaviano, Benz, Scheffler, Benini, 2023) provides "an open-source FPGA implementation of Cheshire, currently targeting Digilent's Genesys II board" but gives no FPGA frequency. Its numbers are for the Neo ASIC (TSMC 65 nm, up to 325 MHz). — [arXiv 2305.04760](https://arxiv.org/abs/2305.04760)
- The Culsans paper (DSD/SEAA 2024 WiP) gives no FPGA frequency in its text. Its repository's Genesys2 flow generates a 50 MHz core clock. — [arXiv 2407.19895](https://arxiv.org/abs/2407.19895); [culsans run.tcl](https://github.com/pulp-platform/culsans/blob/master/fpga/xilinx/xlnx_clk_gen/tcl/run.tcl)
- The Ara2 paper (arXiv 2311.07493) has no CVA6 FPGA frequency. The Ara README says Ara "can be currently implemented on VCU128 and VCU118" through Cheshire's flow, and Ara's Cheshire device-tree patch sets 50 MHz. — [arXiv 2311.07493](https://arxiv.org/abs/2311.07493); [Ara README](https://github.com/pulp-platform/ara/blob/main/README.md); [device_tree.patch](https://github.com/pulp-platform/ara/blob/main/cheshire/patches/device_tree.patch)
- ETH maintainer M. Schaffner (2019): "We currently use 60 MHz for the Kintex7 FPGA mappings (both the standalone version from this repository and on OpenPiton). The FPU fix will allow us to use the FPU at that frequency as well (previously we had to lower to 30MHz with FPU enabled)." — [CVA6 issue #226](https://github.com/openhwfoundation/cva6/issues/226)
- F. Zaruba (2018): "I do remember that I was closing timing at approximately 50 MHz on a Virtex 7." — [CVA6 issue #77](https://github.com/openhwfoundation/cva6/issues/77)
- The Ariane v4.1.0 changelog (the release with "Official support for floating point unit") says: "Reduce clock frequency of FPGA to 30 MHz to accomodate FPU". — [CHANGELOG.md](https://github.com/openhwgroup/cva6/blob/master/CHANGELOG.md)
- The OpenSBI "Ariane FPGA SoC Platform" doc says the platform supports only the Genesys 2 board and gives no frequency. — [OpenSBI fpga-ariane.md](https://qemu.googlesource.com/opensbi/+/refs/heads/master/docs/platform/fpga-ariane.md)

### Inferences
- The upstream flow's 50 MHz is a conservative Kintex-7 setting inherited since about 2019. The maintainers' own numbers (60 MHz on K7 after the FPU fix) suggest it carries margin even on 7-series.

### Gaps
- The published TVLSI version was not checked separately from arXiv 1904.05442. It is presumed identical with respect to FPGA content.
- The Carfield journal paper's FPGA section (if any) was not retrieved. The 50 MHz figure comes from the repository only.

---

## Q2. PULP platform SoCs using CVA6 on FPGA (Cheshire, Carfield, Culsans, Ara, Occamy, others): CVA6 clock per board

### Takeaway
Every PULP SoC flow found clocks CVA6 at 50 MHz or less on both Genesys2 (Kintex-7) and VCU118/VCU128 (Virtex US+). Cheshire, Carfield, Ara and Culsans use 50 MHz. Occamy's CVA6 host on VCU128 runs at 25 MHz, and the KU Leuven Occamy derivative HeMAiA at about 41.7 MHz.

### Cited Findings
- Cheshire `impl_ip.tcl` configures `clk_wiz` with `CLKOUT1_REQUESTED_OUT_FREQ {50.000}` for genesys2 (200 MHz input), vcu128 (100 MHz input) and vcu118 (250 MHz input). The VCU118/VCU128 XDCs set `SOC_TCK 20.0` on `clk_50`. — [impl_ip.tcl](https://github.com/pulp-platform/cheshire/blob/main/target/xilinx/scripts/impl_ip.tcl); [vcu118.xdc](https://github.com/pulp-platform/cheshire/blob/main/target/xilinx/constraints/vcu118.xdc); [vcu128.xdc](https://github.com/pulp-platform/cheshire/blob/main/target/xilinx/constraints/vcu128.xdc)
- Cheshire FPGA parts: genesys2 `xc7k325tffg900-2`, vcu128 `xcvu37p-fsvh2892-2L-e`, vcu118 `xcvu9p-flga2104-2L-e`. The default CVA6 target is `cv64a6_imafdchsclic_sv39_wb`. — [common.tcl](https://github.com/pulp-platform/cheshire/blob/main/target/xilinx/scripts/common.tcl); [cheshire.mk](https://github.com/pulp-platform/cheshire/blob/main/cheshire.mk)
- Community report (PULP forum, Oct 2024 to Nov 2025): a dual-core Cheshire v0.1.0 build on Genesys2 (Vivado 2023.2) failed with "timing constraints are not met", and USB had to be removed to fit. A maintainer suggested relaxing constraints. Another user used a VCU118 port of Cheshire. No frequency or WNS was given. — [PULP forum thread](https://pulp-platform.org/community/showthread.php?pid=1000)
- Carfield supports VCU128 (default, `xcvu37p-fsvh2892-2L-e`) and VCU118 (`xcvu9p-flga2104-2L-e`). Its host clock is `SOC_TCK 20` (50 MHz, `clk_50`), and the block-design flavour generates 10/20/50 MHz outputs. — [xilinx.mk](https://github.com/pulp-platform/carfield/blob/main/target/xilinx/xilinx.mk); [carfield.xdc](https://github.com/pulp-platform/carfield/blob/main/target/xilinx/constraints/carfield.xdc); [carfield_bd_vcu118.tcl](https://github.com/pulp-platform/carfield/blob/main/target/xilinx/flavor_bd/scripts/carfield_bd_vcu118.tcl)
- Carfield's run script comment: "Runtime optimized due to the low frequency (50/20MHz)". — [flavor_vanilla run.tcl](https://github.com/pulp-platform/carfield/blob/main/target/xilinx/flavor_vanilla/scripts/run.tcl)
- Culsans' Genesys2-only FPGA flow ("hard-coded to Genesys 2 for the moment") uses a CVA6 clock of 50 MHz. — [run.tcl](https://github.com/pulp-platform/culsans/blob/master/fpga/scripts/run.tcl); [clk_gen run.tcl](https://github.com/pulp-platform/culsans/blob/master/fpga/xilinx/xlnx_clk_gen/tcl/run.tcl)
- Ara: CVA6 + Ara on VCU128/VCU118 through Cheshire's flow, at 50 MHz. — [Ara README](https://github.com/pulp-platform/ara/blob/main/README.md); [device_tree.patch](https://github.com/pulp-platform/ara/blob/main/cheshire/patches/device_tree.patch)
- Occamy on VCU128: the CVA6 host DTS entry is `compatible = "eth,ariane"`, `clock-frequency = <25000000>`, `riscv,isa = "rv64fimafd"`, `mmu-type = "riscv,sv39"`. The block design's clk_wiz outputs are 100, 25, 12.5 and 120 MHz. The README notes the default Occamy configuration "is too large for the VCU128" and must be reduced to 1 quadrant / 1 cluster. — [occamy.dts](https://github.com/pulp-platform/occamy/blob/main/target/fpga/bootrom/occamy.dts); [occamy_vcu128_bd.tcl](https://github.com/pulp-platform/occamy/blob/main/target/fpga/occamy_vcu128_bd.tcl); [FPGA README](https://github.com/pulp-platform/occamy/blob/main/target/fpga/README.md)
- A third-party Occamy-based hypervisor platform's DTS uses CVA6 `clock-frequency = <50000000>`, which suggests some Occamy FPGA builds ran at 50 MHz. — [CVA6-Hypervisor-Platform occamy.dts](https://github.com/maskedarray/CVA6-Hypervisor-Platform/blob/main/linux/occamy.dts)
- HeMAiA (KU Leuven) on VCU128: `create_clock -period 4.0 -name clk_main`, with `clk_core` generated `-divide_by 6`, i.e. 41.67 MHz. — [hemaia_system_vcu128_impl.xdc](https://github.com/KULeuven-MICAS/HeMAiA/blob/main/target/fpga/hemaia_system/hemaia_system_vcu128_impl.xdc)
- HERO: "A second implementation target currently under development is Xilinx' VCU128, where a 64-bit RISC-V CVA6 host CPU and a multi-core 32-bit RISC-V accelerator are combined". No frequency is given. — [HERO README](https://github.com/pulp-platform/hero)

### Inferences
- PULP flows use 50 MHz as a portable, low-effort default, even on Virtex US+ boards that could likely run faster. The Carfield comment explicitly ties the low frequency to fast runtimes. These numbers should not be read as maximum achievable frequency on US+.

### Gaps
- No PULP paper reports an achieved fmax for CVA6 on VCU118/VCU128.
- The `maskedarray` repo's branch name (`main`) was not verified. The link may need `/blob/master/`.

---

## Q3. OpenPiton + Ariane (Princeton): Genesys2, VC707, VCU118, XUPP3R, AWS F1, Alveo

### Takeaway
OpenPiton's board table sets 66.667 MHz on Genesys2, 60 MHz on VC707, 30 MHz on Nexys Video, **100 MHz on VCU118**, 60 MHz on XUPP3R (VU9P) and 62.5 MHz on AWS F1. The SMAPPIC paper reports Ariane-based multi-tile prototypes on F1 at 100 MHz (75 MHz for the fullest configurations). No source checked here documents timing reports, and OpenPiton+Ariane's FPU status at the time of those builds is ambiguous.

### Cited Findings
- `block.list`, `system` design: `vc707,60,1024;genesys2,66.667,1024;nexysVideo,30,512;vcu118,100,2048;xupp3r,60,32768`; `piton_aws`: `f1,62.5,4096`. — [block.list](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/piton/tools/src/proto/block.list)
- The VCU118 `clk_mmcm.xci` sets CLKOUT1 = 100 MHz. Genesys2 sets 66.666 and VC707 sets 60.000. FPGA parts: VCU118 `xcvu9p-flga2104-2L-e`, XUPP3R `xcvu9p-flgb2104-2-e`, F1 `xcvu9p-flgb2104-2-i`. — [vcu118 clk_mmcm.xci](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/piton/design/chipset/xilinx/vcu118/ip_cores/clk_mmcm/clk_mmcm.xci); [proto/vcu118/board.tcl](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/piton/tools/src/proto/vcu118/board.tcl)
- The Ariane bitfile is built with `protosyn -b genesys2 -d system --core=ariane --uart-dmw ddr`. The README section is titled "Support for the Ariane RV64IMAC Core". — [OpenPiton README](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/README.md)
- The currently pinned Ariane submodule (`4c01614`) has `RVF = riscv::IS_XLEN64`, `RVD = riscv::IS_XLEN64` under `ifdef PITON_ARIANE`, so F/D are on for 64-bit. Its `cv64a6_imafdc_sv39_openpiton_config_pkg.sv` sets `CVA6ConfigFpuEn = 1`. — [ariane_pkg.sv @4c01614](https://github.com/openhwgroup/cva6/blob/4c01614f83cd9dd91d115aa190bd4fc6a284b59e/core/include/ariane_pkg.sv); [config pkg @4c01614](https://github.com/openhwgroup/cva6/blob/4c01614f83cd9dd91d115aa190bd4fc6a284b59e/core/include/cv64a6_imafdc_sv39_openpiton_config_pkg.sv)
- The 2017 release notes say: "Increasing system frequency on Genesys2 to 66.67MHz" and "Decreasing system frequency on VC707 to 60MHz to better guarantee that implementation meets timing". — [OpenPiton Release 5](https://openpiton-blog.princeton.edu/2017/06/openpiton-release-5)
- OpenPiton+Ariane slides (2019): Genesys2 "1-2 cores at 66MHz", VC707 "1-4 cores at 60MHz", Nexys Video "1 core at 30MHz". VCU118 and BittWare XUPP3R were "In progress", ">100MHz". — [opariane-wosh.pdf](https://pulp-platform.org/docs/riscv_workshop_zurich/opariane-wosh.pdf)
- BYOC (ASPLOS'20): "Both of our experimental platforms were implemented at 66.67 MHz on a Digilent Genesys2 board". The single-core LUT breakdown covers "Ariane with or without FPU". The introduction says BYOC can be "realised on FPGA (at ~100MHz)". — [BYOC PDF](https://par.nsf.gov/servlets/purl/10201514)
- SMAPPIC (ASPLOS'23), AWS F1: Table 2 lists "Frequency 100 MHz, Core Ariane", RISC-V 64-bit, Linux v5.12. Table 4 gives 1x12 → 75 MHz (97% LUT), 1x10 → 100 MHz (83%), 2x4 → 100 MHz (73%), 2x5 → 75 MHz (88%), 4x2 → 100 MHz (87%). The text adds "full-stack Linux at speeds around 100 MHz". — [SMAPPIC PDF](https://par.nsf.gov/servlets/purl/10470689)
- CVA6 issue #2700 (2025): the OpenPiton configuration of CVA6 (`cv64a6_imacfdc_sv39_openpiton`) "cannot boot Linux" on UltraScale+ FPGAs but works on Genesys2. J. Balkind suspects "a specific timing component". At the CVA6 meeting, J.-R. Coulon noted "MMU was often in the critical path of the Genesys 2 board". — [issue #2700](https://github.com/openhwfoundation/cva6/issues/2700)
- A user (jctullos, 2020) reported getting "the VCU118 build working for openpiton with ariane" without stating a frequency. — [issue #516](https://github.com/openhwfoundation/cva6/issues/516)
- BSC extended OpenPiton to Alveo U280 and U55C (MEEP). No frequency was found. — [BSC "Extensions to OpenPiton"](https://bsc.es/node/63755)

### Inferences
- OpenPiton's 100 MHz on VCU118 and SMAPPIC's 100 MHz on F1 are the only published ≥100 MHz CVA6 figures on US+. They are system-wide clocks with OpenPiton's own cache hierarchy. The CVA6 version, the FPU setting in those builds, and timing-closure status are not documented. SMAPPIC's choice of 75 MHz for its densest configurations suggests 100 MHz was close to the edge.
- `block.list` gives XUPP3R and F1 (both VU9P, -2) only 60–62.5 MHz, while VCU118 (VU9P -2L) gets 100 MHz. This suggests board/shell factors (e.g. the F1 shell, SLR crossings) or older settings matter as much as the core.

### Gaps
- No Alveo (U200/U250/U280/U55C) frequency for OpenPiton+Ariane was found. The BSC/MEEP and OpenHW Polara (U280) sources did not expose a clock value. The GitHub mirror of `core-v-polara-apu` has the same `block.list` as OpenPiton, without U280.
- Whether the VCU118 100 MHz setting closes timing with the FPU-enabled CVA6 (post-2020 OpenPiton) is unverified. Issue #2700 hints at UltraScale+-specific failures.

---

## Q4. ESP (Columbia) Ariane/CVA6 tile: frequency on VCU118/VCU128/VC707/proFPGA

### Takeaway
ESP clocks its tiles, including the Ariane CPU tile, from a MIG auxiliary clock: **~78 MHz on VCU118 (VU9P), proFPGA VU440 and proFPGA VU19P, 75 MHz on VCU128**, and 50 MHz on VC707. On ZCU102/ZCU106 the tile reference clock is the PS `pl_clk0` at 75 MHz. ESP's Ariane fork has the FPU enabled (RVF = RVD = 1).

### Cited Findings
- VCU118 `ariane/mig.tcl`: `CONFIG.C0.DDR4_TimePeriod {1600}`, `CONFIG.C0.DDR4_InputClockPeriod {4000}`, `CONFIG.ADDN_UI_CLKOUT1_FREQ_HZ {78}`. — [mig.tcl](https://github.com/sld-columbia/esp/blob/main/constraints/xilinx-vcu118-xcvu9p/ariane/mig.tcl)
- In VCU118 `top.vhd`, MIG `ui_clk => clkm` and `ui_clk_slow => chip_refclk`. Tiles receive `refclk => chip_refclk`, memory tiles get `sys_clk(0) <= clkm`. The simulation model toggles `chip_refclk` every 6.4 ns (78.125 MHz) and `clkm` every 3.2 ns (156.25 MHz). — [top.vhd](https://github.com/sld-columbia/esp/blob/main/socs/xilinx-vcu118-xcvu9p/top.vhd)
- VCU128 `ariane/mig.tcl`: `ADDN_UI_CLKOUT1_FREQ_HZ {75}`. The proFPGA VU440 and VU19P `mig.tcl` use `{78}`. — [vcu128 mig.tcl](https://github.com/sld-columbia/esp/blob/main/constraints/xilinx-vcu128-xcvu37p/ariane/mig.tcl); [constraints tree](https://github.com/sld-columbia/esp/tree/main/constraints)
- ZCU102 and ZCU106 `zynq.tcl`: `PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {75}`. In `zynqmp_top_wrapper.vhd`, `pl_clk0 => chip_refclk`. — [zcu102 zynq.tcl](https://github.com/sld-columbia/esp/blob/main/constraints/xilinx-zcu102-xczu9eg/zynq.tcl); [zynqmp_top_wrapper.vhd](https://github.com/sld-columbia/esp/blob/main/socs/xilinx-zcu102-xczu9eg/zynqmp_top_wrapper.vhd)
- VC707 `top.vhd`: `clkgen generic map (CFG_FABTECH, 16, 32, ...)` derives `chip_refclk` from `clkm` (100 MHz MIG `ui_clk`), i.e. ×16/÷32 = 50 MHz. — [vc707 top.vhd](https://github.com/sld-columbia/esp/blob/main/socs/xilinx-vc707-xc7vx485t/top.vhd)
- ESP's Ariane submodule (`sld-columbia/ariane` @`21ee234`) sets `RVF = 1'b1`, `RVD = 1'b1` in both the PITON and non-PITON branches. — [ariane_pkg.sv @21ee234](https://github.com/sld-columbia/ariane/blob/21ee2341cd91637ffe2039cfa17a5790c02c4cdb/include/ariane_pkg.sv)

### Inferences
- The per-board frequency was derived from code (MIG auxiliary clock, then `chip_refclk`, then the tiles' `refclk`), not from an ESP document. The mapping of the Ariane CPU tile onto `refclk` follows from the top-level wiring. ESP's dynamic frequency scaling (DFS) options could change the per-tile clock in some configurations.
- ESP's 75–78 MHz figures show that a group with years of US+ experience settled below 100 MHz for an FPU-enabled Ariane tile on VU9P/VU37P. That is consistent with the user's 90.9 MHz on a K26 being already good.

### Gaps
- No ESP paper or doc statement explicitly saying "Ariane runs at 78 MHz on VCU118" was found (web search returned nothing). This is code-derived.
- ESP's ZCU102/ZCU106 SoCs: whether an Ariane tile is supported/used there was not verified.

---

## Q5. Community and company ports to Zynq UltraScale+, Alveo, AWS F1 and Versal (ZCU102/104/106, Ultra96, KV260/KR260, Alveo, F1, VCK190)

### Takeaway
Public CVA6 ports to Zynq US+ and Kria are rare. GitHub repository search found **no KV260, KR260, ZCU104, Ultra96 or VCK190 CVA6 port that reports a frequency**. One KR260 project lists FPGA bring-up as future work. The ports that do exist (ZCU102 automotive MCU, VU33P PCIe card, VCU118 accelerator SoC, U55C, AXKU5) use 25–50 MHz for the CVA6 domain. The one explicitly documented attempt at 100 MHz with `cv64a6_imafdc_sv39` on Virtex US+ (FK33) fell back to 50 MHz.

### Cited Findings
- Cuomo et al. (2023): RV64GC CVA6 MCU on the ZCU102 PL, "synthesized on the PL targeting 50 MHz frequency". The core is real-time-enhanced, not unmodified. — [arXiv 2307.04148](https://arxiv.org/abs/2307.04148)
- cva6_fk33 (SQRL Forest Kitten 33, `xcvu33p-fsvh2104-2-e`): "CVA6 clock frequency (MHz). Heavy configs can't close at 100 MHz". `ifeq ($(TARGET_CFG),cv64a6_imafdc_sv39) CPU_FREQ_MHZ ?= 50 else CPU_FREQ_MHZ ?= 100`. — [Makefile](https://github.com/aebarthyi/cva6_fk33/blob/main/Makefile)
- cva6_fk33's flow enables `STEPS.SYNTH_DESIGN.ARGS.RETIMING true` and the `ExtraTimingOpt` placement directive, and runs a pre-opt hook. — [vivado.tcl](https://github.com/aebarthyi/cva6_fk33/blob/main/vivado/vivado.tcl)
- The pre-opt hook says: "FPnew pipeline regs broadcast into the EX/issue flush logic and dominate WNS at 50 MHz. FPnew puts (* keep *) on its pipeline regs to preserve pipeline depth — clear those so opt_design / phys_opt are free to clone and pack". It also sets `MAX_FANOUT 8`. — [pre_opt_design.tcl](https://github.com/aebarthyi/cva6_fk33/blob/main/vivado/pre_opt_design.tcl)
- FleXNNgine-CVA6 on VCU118 (`xcvu9p-flga2104-2L-e`, `cv64a6_imafdch_sv39_wb`): the system clock is 50 MHz ("CVA6 + AXI + PE array") and the accelerator domain runs at 250 MHz. — [clock_uplift.xdc](https://github.com/FoivosParaskevas/FleXNNgine-CVA6/blob/main/fpga/scripts/clock_uplift.xdc); [fpga/Makefile](https://github.com/FoivosParaskevas/FleXNNgine-CVA6/blob/main/fpga/Makefile)
- SoC-all-core (ZCU102, `xczu9eg-ffvb1156-2-e`): `cv32a6_imac_sv0` at a 40 MHz default. The README says to measure fmax by changing `clk_wiz_0` and reading WNS ("fmax = 1000 / (period in ns - WNS)") but reports no number. — [README](https://github.com/thanhtruong332/SoC-all-core/blob/main/README.md)
- corejack: CVA6 on Alinx AXKU5 (Kintex US+), Zephyr DTS at 25 MHz. The README says both board targets are "hardware-validated". — [corejack](https://github.com/patrickerich/corejack)
- CHORYS (Alveo U55C): the CVA6 top's clk_wiz comment gives `clk_out1 ( clk ), // 50 MHz`. The file is named `u55_cva6_sim.sv`. — [u55_cva6_sim.sv](https://github.com/FriedDede/CHORYS_RISCV-V/blob/master/hw/tops/u55_cva6_sim.sv)
- KR260 project (turing-house-community): `cv64a6_imafdc_sv39` with custom instructions, verified in Verilator only. "FPGA bring-up on the Kria KR260" is under "What's next". — [README](https://github.com/turing-house-community/multicore-on-fpga/blob/main/README.md)
- VCU118 ports of the stock CVA6 APU: jctullos (2020) used `CLK_PERIOD_NS := 20` (50 MHz) on `xcvu9p-flga2104-2L-e`. Others (issue #2413, 2024) ported by retargeting the Genesys2 project in the Vivado GUI and did not state a frequency. — [jctullos commit](https://github.com/jctullos/cva6/commit/7c290d1b22cd57645555440f88dbba1295b46ed5); [issue #2413](https://github.com/openhwfoundation/cva6/issues/2413)
- AWS F1: OpenPiton+Ariane (62.5 MHz target in `block.list`) and SMAPPIC (75–100 MHz reported), as above. A separate "opensource ariane based SoC on aws-fpga" (merledu/nova, 2022) was found, but no frequency was extracted. — [block.list](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/piton/tools/src/proto/block.list); [SMAPPIC](https://par.nsf.gov/servlets/purl/10470689); [merledu/nova](https://github.com/merledu/nova)
- Versal: HeMAiA has a VPK180 (`xcvp1802-lsvc4072-2MP-e`) target containing a CVA6 host, but its CVA6 clock was not determined. No VCK190 CVA6 port was found. — [HeMAiA](https://github.com/KULeuven-MICAS/HeMAiA)

### Inferences
- The user's KR260 result (unmodified `cv64a6_imafdc_sv39`, 90.9 MHz met) appears to be **higher than any publicly documented CVA6 frequency on a Zynq US+ / Kria part**. The only published Zynq US+ CVA6 numbers are 40–50 MHz (ZCU102), and they are conservative defaults, not fmax searches.

### Gaps
- GitHub search was limited by API rate limits. Queries such as "cva6 zcu102/zcu104/kv260/kria/alveo/vck190" returned no relevant repos, but repos that mention boards only inside files would be missed.
- No vendor/company (e.g. Thales, Hensoldt Cyber, 10xEngineers) public report of CVA6 on Zynq US+, Alveo or Versal with a frequency was found.

---

## Q6. Reports of 64-bit CVA6 with FPU closing ≥100 MHz on UltraScale+ without RTL changes, and what limits it

### Takeaway
No source shows unmodified 64-bit CVA6 with FPU **verified** (timing report) at ≥100 MHz on UltraScale+. The closest are OpenPiton's VCU118 setting and SMAPPIC's F1 prototypes at 100 MHz (OpenPiton variant, FPU status unclear) and maintainer expectations ("100 MHz should be possible on Ultrascale+", 2021; "around 150MHz on a Virtex UltraScale+ device (SG2)", 2018, before the FPU existed). The limiters cited are the FPnew FMA/pipeline registers that Vivado fails to retime, FPU-to-flush/issue fan-out, and the MMU/TLB path.

### Cited Findings
- 2018 expectation, before FPU integration: "In terms of operating frequency, I expect the Ariane design to close around 150MHz on a Virtex UltraScale+ device (SG2)". The asynchronous reset costs "~4% slower, <0.5% more logic". — [issue #77](https://github.com/openhwfoundation/cva6/issues/77)
- 2019: "so far we could not really get it [register retiming of FPnew output regs] working well with the Vivado FPGA flow… You can expect that the complete mapping runs around 60MHz on a Kintex-7 (Genesys2). 100MHz is a bit too tight, even without FPU." — [issue #226](https://github.com/openhwfoundation/cva6/issues/226)
- 2021, F. Zaruba: "the retiming in Vivado is still quite weak compared to Synopsys. The FPU now has a version with naïvely distributed registers which should perform a bit better on the FPGA. 100 MHz should be possible on Ultrascale+ devices." This is an expectation, not a measurement. — [issue #226](https://github.com/openhwfoundation/cva6/issues/226)
- 2025, issue #2895 (XC7VX485T, FD enabled): long datapath in `fpnew_fma.sv` (53-bit mantissa product). Two users fixed their FPU timing by pre-synthesizing the FMA/FPU wrapper out-of-context with `-retiming` and importing the DCP: "So i essentially created a new wrapper for the FPU, synthesized it with -retiming and -mode out_of_context and then imported the dcp." — [issue #2895](https://github.com/openhwfoundation/cva6/issues/2895)
- 2026, cva6_fk33 on VU33P: FPnew pipeline registers "dominate WNS at 50 MHz" because they fan out into EX/issue flush logic. The author removed KEEP/DONT_TOUCH on `i_fpnew_cast_multi*mid_pipe*` regs and set `MAX_FANOUT 8`, yet still defaults imafdc to 50 MHz ("Heavy configs can't close at 100 MHz"). — [pre_opt_design.tcl](https://github.com/aebarthyi/cva6_fk33/blob/main/vivado/pre_opt_design.tcl); [Makefile](https://github.com/aebarthyi/cva6_fk33/blob/main/Makefile)
- MMU: "@JeanRochCoulon mentions that MMU was often in the critical path of the Genesys 2 board" (CVA6 meeting, Jan 2025). — [issue #2700](https://github.com/openhwfoundation/cva6/issues/2700)
- In the CVA6-H DSE, the fully-associative L1 TLB "implemented as a full combinational circuit" makes the design "not optimized for this particular FPGA architecture". Going from 16 to 64 TLB entries cost "50% increase in the FPGA resources". — [arXiv 2302.02969](https://arxiv.org/abs/2302.02969)
- CVA6S+ (2025) enables "an optional Load Unit output register… to improve timing closure, adding one cycle of latency for load operations" on its Genesys 2 (Kintex-7) FPGA implementation, which points to the load path as another FPGA critical path. — [arXiv 2505.03762](https://arxiv.org/abs/2505.03762)
- Counter-datum: the CVA6-H paper states its experiments ran "targeting the Genesys2 FPGA at 100MHz" (Kintex-7, -2). This contradicts maintainer statements that 100 MHz is "too tight" on Kintex-7. — [arXiv 2302.02969](https://arxiv.org/abs/2302.02969); contradicted by [issue #226](https://github.com/openhwfoundation/cva6/issues/226)
- Issue #3104 (2025, ASIC Design Compiler, 14 nm at 500 MHz, and 28 nm at 0.8 ns) lists many violating paths in `pmp`, `fpnew` and `csr_regfile` for `cv64a6_imafdc_sv39`. This is ASIC context, but the same modules show up. — [issue #3104](https://github.com/openhwfoundation/cva6/issues/3104)

### Inferences
- The user's failing margin at 100 MHz (WNS −0.553 ns) is small. Its implied fmax is 1000/(10 + 0.553) ≈ **94.8 MHz** (simple arithmetic from the user's own data). The FPU-specific techniques documented by others (removing KEEP on FPnew pipeline registers so Vivado can retime or replicate them, OOC-synthesizing `fpnew_fma` with `-retiming`, or limiting fan-out from FPU pipeline registers into flush logic) are the community's known levers. Whether they recover 0.55 ns on a K26 -2LV is untested here.
- The CVA6-H "Genesys2 at 100MHz" claim may refer to a target or reference clock rather than a met constraint, since no timing data is shown. It should not be used as evidence that unmodified CVA6 closes 100 MHz on 7-series without checking the authors' repository.

### Gaps
- No public post-route timing report of unmodified `cv64a6_imafdc_sv39` at ≥100 MHz on any UltraScale+ device was found.
- No source quantifies the K26 `-2LV` speed relative to the `-2`/`-2L` VU9P/VU37P parts used by OpenPiton, ESP and PULP. AMD's data sheets (e.g. DS925 for Zynq US+) would be needed. The "LV" operating point is a low-voltage (slower) grade, which would make the user's 90.9 MHz comparatively strong; this was not verified here.

---

## Q7. Summary: typical frequency range for 64-bit CVA6 with FPU on UltraScale+, and whether 90.9 MHz is in line

### Takeaway
For 64-bit CVA6 with FPU on UltraScale+, reported or configured frequencies cluster at **50 MHz** (PULP Cheshire, Carfield, Ara, FleXNNgine, the FK33 default, jctullos, the ZCU102 automotive MCU), with outliers of **25–42 MHz** (Occamy, HeMAiA) and a higher tier of **75–78 MHz** (ESP on VU9P/VU37P/VU19P/ZU+). Only OpenPiton/SMAPPIC reach **100 MHz** on VU9P, in an OpenPiton tile with unverified FPU status and no timing reports. **The user's 90.9 MHz with unmodified `cv64a6_imafdc_sv39` on a K26 (-2LV) is at or above the top of the documented range for a stock CVA6 APU-style integration.** It exceeds every documented Zynq US+ / Kria number found (40–50 MHz) and sits just below the OpenPiton/SMAPPIC 100 MHz figures.

### Cited Findings
- 50 MHz: Cheshire VCU118/VCU128 ([impl_ip.tcl](https://github.com/pulp-platform/cheshire/blob/main/target/xilinx/scripts/impl_ip.tcl)); Carfield VCU118/VCU128 ([carfield.xdc](https://github.com/pulp-platform/carfield/blob/main/target/xilinx/constraints/carfield.xdc)); Ara VCU128/VCU118 ([device_tree.patch](https://github.com/pulp-platform/ara/blob/main/cheshire/patches/device_tree.patch)); FleXNNgine VCU118 ([clock_uplift.xdc](https://github.com/FoivosParaskevas/FleXNNgine-CVA6/blob/main/fpga/scripts/clock_uplift.xdc)); FK33 VU33P imafdc default ([Makefile](https://github.com/aebarthyi/cva6_fk33/blob/main/Makefile)); ZCU102 automotive MCU ([arXiv 2307.04148](https://arxiv.org/abs/2307.04148)); jctullos VCU118 ([commit](https://github.com/jctullos/cva6/commit/7c290d1b22cd57645555440f88dbba1295b46ed5)).
- 25 MHz and ~41.7 MHz: Occamy VCU128 ([occamy.dts](https://github.com/pulp-platform/occamy/blob/main/target/fpga/bootrom/occamy.dts)); HeMAiA VCU128 ([xdc](https://github.com/KULeuven-MICAS/HeMAiA/blob/main/target/fpga/hemaia_system/hemaia_system_vcu128_impl.xdc)).
- 75–78 MHz: ESP VCU118/proFPGA VU440/VU19P (78), VCU128 (75), ZCU102/ZCU106 PL (75) ([ESP constraints](https://github.com/sld-columbia/esp/tree/main/constraints)).
- 60–62.5 MHz: OpenPiton XUPP3R and AWS F1 ([block.list](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/piton/tools/src/proto/block.list)).
- 100 MHz: OpenPiton VCU118 ([block.list](https://github.com/PrincetonUniversity/openpiton/blob/openpiton/piton/tools/src/proto/block.list)); SMAPPIC F1 (100 MHz for ≤87% LUT configs, 75 MHz at 88–97% LUT) ([SMAPPIC](https://par.nsf.gov/servlets/purl/10470689)).
- Expectations, not measurements: "100 MHz should be possible on Ultrascale+ devices" (2021); "around 150MHz on a Virtex UltraScale+ device (SG2)" (2018, before the FPU). — [issue #226](https://github.com/openhwfoundation/cva6/issues/226); [issue #77](https://github.com/openhwfoundation/cva6/issues/77)
- Explicit failure report: a VU33P port says heavy configs (`cv64a6_imafdc_sv39`) "can't close at 100 MHz". — [cva6_fk33 Makefile](https://github.com/aebarthyi/cva6_fk33/blob/main/Makefile)

### Inferences
- **Verdict for the user:** 90.9 MHz met, with an implied ~94.8 MHz fmax, is consistent with what others get and better than most published setups. It is in line with maintainer expectations that "~100 MHz should be possible on UltraScale+". It also agrees with an independent 2026 VU33P port that could not close 100 MHz with the same configuration. Missing 100 MHz by 0.55 ns on a low-voltage K26 part is unsurprising.
- Most published numbers are conservative defaults chosen for portability or build time, not fmax searches. So "typical" (50 MHz) understates what US+ can do. The meaningful comparison set is ESP (75–78 MHz), OpenPiton/SMAPPIC (100 MHz) and FK33 (fails 100 MHz). The user's result sits inside that 75–100 MHz band.
- Reaching ≥100 MHz would likely require FPGA-specific measures already used by others: FPnew register retiming or KEEP removal, OOC retimed FMA, fan-out control on FPU→flush paths, and possibly the MMU/TLB or load-path registers noted by the CVA6 team and the CVA6S+ authors. Some of these are tool-only changes, not RTL changes.

### Gaps
- No apples-to-apples data exists (same CVA6 version, same config, same tool version, US+ part, published timing report).
- The Dörflinger et al. CF'21 Virtex US+ comparison (Vivado 2019.2) likely contains a CVA6 FPGA frequency but could not be retrieved, so it should be obtained manually.
