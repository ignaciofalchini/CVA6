# What the official CVA6 project (OpenHW, formerly pulp-platform/ariane) says and does about FPGA clock frequency and timing

Research date: 2026-10-27. Primary method: a clone of the official repo (`github.com/openhwgroup/cva6`, which GitHub now redirects to `github.com/openhwfoundation/cva6`), read at `master` HEAD `742dc82a` (2026-10-23), plus a read of GitHub issues, PRs and discussions through the `gh` API, plus RISC-V Summit Europe proceedings PDFs.

Repository status notes (verified):
- The repository is now `openhwfoundation/cva6`; `openhwgroup/cva6` URLs redirect to it ([gh repo view](https://github.com/openhwfoundation/cva6)).
- On 2026-10-23 the README was changed to say `master` "is protected and does not accept new pull requests… Please direct new contributions to the `main` branch" (commit 742dc82a, PR #3664) — [README @742dc82a](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/README.md). A `master_candidate` branch exists, and open PR #3675 (2026-10-27) restructures its targets: see Q2.

Abbreviation: `R@HEAD` means `https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/`.

---

## Q1. Which clock frequency does the official CVA6/Ariane FPGA flow use on each board, how has it changed, and does Linux boot at that frequency?

### Takeaway
The official Xilinx flow clocks the core at **50 MHz** on Genesys2, KC705 and VC707 (all 7-series) and at **25 MHz** on Nexys Video (Artix-7). This holds for every configuration, including the FPU-equipped `cv64a6_imafdc_sv39`, and Linux boots at these frequencies. The official Intel/Altera flow on the **Agilex 7** dev kit runs at **100 MHz**; it was lowered from 200 MHz in Feb 2025 "to avoid timing issues in 64bit version". No UltraScale/UltraScale+ board is supported in today's Makefile. Only leftover VCU118 code from 2018 remains. The official flow uses "RuntimeOptimized" place-and-route and its CI never checks timing.

### Cited Findings
**Current frequencies (master HEAD, Oct 2026)**
- Makefile: `BOARD ?= genesys2`. Genesys2 is `xc7k325tffg900-2` with `CLK_PERIOD_NS := 20`. KC705 is `xc7k325tffg900-2` with `20`. VC707 is `xc7vx485tffg1761-2` with `20`. Nexys Video is `xc7a200tsbg484-1` with `40`. The comment lists only "kc705, genesys2, nexys_video" as supported — [Makefile](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/Makefile)
- The real core clock comes from the `xlnx_clk_gen` Clocking Wizard script. For Nexys Video: `PRIM_IN_FREQ 100`, `CLKOUT1_REQUESTED_OUT_FREQ {25}` (core), 125/125(90°)/50/200 for the other outputs. For every other board: `PRIM_IN_FREQ 200`, `CLKOUT1 {50}` (core), 125, 125 (90°) and 50 MHz — [xlnx_clk_gen/tcl/run.tcl](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/corev_apu/fpga/xilinx/xlnx_clk_gen/tcl/run.tcl). In `ariane_xilinx.sv` the instance is commented `.clk_out1 ( clk ), // 50 MHz` (or `// 25 MHz` for Nexys Video, whose clk_in1 is the 100 MHz `ddr_clock_out`) — [ariane_xilinx.sv](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/corev_apu/fpga/src/ariane_xilinx.sv)
- Verified by grep in the clone: `CLK_PERIOD_NS` is only defined in the top Makefile and in `corev_apu/fpga/sourceme.sh`, then passed to the sub-make. No `.tcl`, `.xdc` or `.sdc` file in the repo reads it. So in the Xilinx flow it only documents the frequency; `xlnx_clk_gen` actually sets it — [Makefile](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/Makefile), [sourceme.sh](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/corev_apu/fpga/sourceme.sh)
- The bootrom/DTS frequencies match. In the bootrom Makefile: Nexys Video `CLOCK_FREQUENCY ?= 25000000`, `PLAT_AGILEX` `100000000`, default `50000000`. `timebase-frequency` is half the core clock — [bootrom/Makefile](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/corev_apu/fpga/src/bootrom/Makefile)
- The official SDK device trees for Linux say the same. `configs/genesys2/cv64a6_imafdc_sv39.dts` and `configs/genesys2/cv32a6_ima_sv32_fpga.dts` have `clock-frequency = <50000000>; // 50 MHz` and `timebase-frequency = <25000000>`. The `configs/agilex7/` versions of both have `clock-frequency = <100000000>; // 100 MHz`. The SDK README says the SDK is "designed and tested for the Digilent Genesys 2 and Agilex 7" — [cva6-sdk genesys2 dts](https://github.com/openhwfoundation/cva6-sdk/blob/master/configs/genesys2/cv64a6_imafdc_sv39.dts), [cva6-sdk agilex7 dts](https://github.com/openhwfoundation/cva6-sdk/blob/master/configs/agilex7/cv64a6_imafdc_sv39.dts), [cva6-sdk README](https://github.com/openhwfoundation/cva6-sdk)
- The FPGA tutorial says: "We currently provide support for the Genesys 2 board and the Agilex 7 Development Kit". It gives no frequency figure — [tutorials/fpga.md](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/tutorials/fpga.md)

**Intel/Altera Agilex 7 (DK-DEV-AGF014E3ES)**
- In `io_pll.tcl` today, `gui_output_clock_frequency0 {100.0}` is the core clock — [io_pll.tcl](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/corev_apu/altera/ip/io_pll.tcl). A stale comment in `cva6_altera.sv` still says `outclk_0 (clk) … 50 MHz` — [cva6_altera.sv](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/corev_apu/altera/src/cva6_altera.sv)
- PR #2790 "Altera fpga update" (Angela Gonzalez Mariño, PlanV, merged 2025-02-25) says it will "Update Altera APU design to support linux in both 32 and 64 bits" and "Reduce the frequency of operation to 100MHz to avoid timing issues in 64bit version". The diff changes `gui_output_clock_frequency0` from `{200.0}` to `{100.0}` (period 5000 ps to 10000 ps) — [PR #2790](https://github.com/openhwfoundation/cva6/pull/2790)
- The tutorial says of Agilex: "We recommend to set the parameter FpgaAlteraEn (and also FpgaEn) to benefit from the FPGA optimizations" — [tutorials/fpga.md](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/tutorials/fpga.md)

**UltraScale+/VCU118**
- `corev_apu/fpga/constraints/vcu118.xdc` (sys_clk 10 ns) and `` `elsif VCU118 `` branches in `ariane_xilinx.sv` date from Florian Zaruba's commit 0ce36534 "Add support for VCU118" (2018-11-12). Today VCU118 is not in the Makefile's board list, in `run.tcl` or in the `xlnx_clk_gen` script. It is effectively unsupported — [vcu118.xdc](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/corev_apu/fpga/constraints/vcu118.xdc), [run.tcl](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/corev_apu/fpga/scripts/run.tcl)
- A user ported to VCU118 in 2024 (#2413, mrbilandi) and got Linux booting after slowing SPI for the SD card ("it takes around 5 minutes to boot Linux"). No core frequency was reported — [issue #2413](https://github.com/openhwfoundation/cva6/issues/2413)

**Official implementation script and constraints**
- `run.tcl` sets `STEPS.SYNTH_DESIGN.ARGS.RETIMING true` and then `steps.place_design.args.directive RuntimeOptimized` and `steps.route_design.args.directive RuntimeOptimized` ("set for RuntimeOptimized implementation"). There is no phys_opt or performance directive — [run.tcl](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/corev_apu/fpga/scripts/run.tcl)
- `ariane.xdc` defines JTAG `tck` at 100 ns and uses `set_max_delay -datapath_only … 20.000` on the `i_dmi_jtag/i_dmi_cdc` CDC paths. It adds a 4-cycle multicycle path from the reset synchronizer ("on the FPGA we do not care about the reset anyway") and `set_property DONT_TOUCH true` on `i_cva6_rvfi`, `i_iti` and `i_encapsulator` — [ariane.xdc](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/corev_apu/fpga/constraints/ariane.xdc)
- The Xilinx top silently overrides the user config for FPGA: `cfg.RVZiCond = 0`, `NrNonIdempotentRules = 1`, `NonIdempotentLength = DRAMBase` — [ariane_xilinx.sv L202-208](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/corev_apu/fpga/src/ariane_xilinx.sv). Issue #3241 (PRugg-Cap, Capabilities Ltd., 2026-03-18, open) complains about this override. It adds: "we've disabled [RVFI] in our fork for FPGA builds as we see it showing up in timing paths" — [issue #3241](https://github.com/openhwfoundation/cva6/issues/3241)

**CI: what is built and booted**
- The GitLab CI `fpga-build` job builds only `TARGET: cv32a6_imac_sv32` with `make fpga`. It reports only utilization: `report_fpga.py` parses `ariane.utilization.rpt` into "kLUTs". There is no timing/WNS check. The `fpga-boot` job is "Test of Linux 32 bits boot on FPGA Genesys2" using `ariane_xilinx_cv32a6_imac_sv32.bit` — [.gitlab-ci.yml](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/.gitlab-ci.yml), [report_fpga.py](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/.gitlab-ci/scripts/report_fpga.py)
- Task #915 "Integrate Linux Boot on FPGA to Thales-CI": "Done for 64b Linux" (jquevremont 2022-09-16). The 32-bit boot came later — [issue #915](https://github.com/openhwfoundation/cva6/issues/915)

**History of the Genesys2 core clock (from `xlnx_clk_gen` and the CHANGELOG)**
- 2018-11-19 (bb821300, Zaruba, "Put batch flow in place"): `CLKOUT1_REQUESTED_OUT_FREQ {50}` from 200 MHz — [commit bb821300](https://github.com/openhwfoundation/cva6/commit/bb821300)
- 2019-02-19 (b1bdc0c0, "Add System Verilog FPU (#163)"): `CLKOUT1 {30}` — [commit b1bdc0c0](https://github.com/openhwfoundation/cva6/commit/b1bdc0c0). The CHANGELOG 4.1.0 says: "Reduce clock frequency of FPGA to 30 MHz to accomodate FPU" — [CHANGELOG.md](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/CHANGELOG.md)
- 2019-03-12 (a5f3184a, #192): back to `CLKOUT1 {50}` — [commit a5f3184a](https://github.com/openhwfoundation/cva6/commit/a5f3184a). Release tags v4.0.0, v4.1.0 and v4.2.0 all have `{50}` (checked via the API). At v4.1.0 `ariane_pkg.sv` has `RVF = 1'b0; RVD = 1'b0`, so the FPU was disabled — [ariane_pkg.sv @v4.1.0](https://github.com/openhwfoundation/cva6/blob/v4.1.0/include/ariane_pkg.sv)
- 2019-04-25/26, Michael Schaffner (ETH) in #226: "You can expect that the complete mapping runs around 60MHz on a Kintex-7 (Genesys2). 100MHz is a bit too tight, even without FPU." Also: "We currently use 60 MHz for the Kintex7 FPGA mappings (both the standalone version from this repository and on OpenPiton). The FPU fix will allow us to use the FPU at that frequency as well (previously we had to lower to 30MHz with FPU enabled)." — [issue #226](https://github.com/openhwfoundation/cva6/issues/226). The repo's clock generator never showed 60 MHz; it stayed at 50.
- 2019-06-25, Zaruba in #270: "Compilation on a 50 MHz, single-issue, in-order core is not a lot of fun" — [issue #270](https://github.com/openhwfoundation/cva6/issues/270)
- 2021-02-05, #608: the user notes "the core frequency is 50 MHz". Zaruba: Linux boot itself takes "around 30" s; most of the ~3 min is loading the kernel over SPI-mode SD (12.5 MHz SPI) — [issue #608](https://github.com/openhwfoundation/cva6/issues/608)
- 2022-10, #976 (0ena, Vivado 2019.2, Genesys2): "increase the base frequency of the CVA6 core from 50MHz to … 53MHz" — [issue #976](https://github.com/openhwfoundation/cva6/issues/976)
- Nexys Video. PR #350 (xushengj, 2019) first used 40 MHz. In the 2022 rebase: "Clock speed for nexys_video is 25MHz instead of 50MHz. We get timing violations when targeting 50MHz." PR #1925 (Saute0212) merged it on 2024-04-04 — [PR #350](https://github.com/openhwfoundation/cva6/pull/350), [PR #1925](https://github.com/openhwfoundation/cva6/pull/1925)
- KC705 (PR #262, 2019-10-09) and VC707 (PR #335, 2019-10-11) were added with `CLK_PERIOD_NS := 20`. They share the 50 MHz `else` branch of the clock generator — [Makefile history](https://github.com/openhwfoundation/cva6/commits/master/Makefile)

**Linux at these frequencies**
- Genesys2 at 50 MHz: Linux boots (CI 32-bit boot job; #915 64-bit; SDK DTS 50 MHz for both `cv64a6_imafdc_sv39` and `cv32a6_ima_sv32_fpga`) — see the citations above.
- Agilex 7 at 100 MHz: PR #2790 explicitly targets Linux on 32 and 64 bits at 100 MHz — [PR #2790](https://github.com/openhwfoundation/cva6/pull/2790)
- Nexys Video at 25 MHz: Red Semi booted 64-bit Linux to a root login in May 2024, after switching to a 4 GB microSD card ("support is experimental") — [issue #2116](https://github.com/openhwfoundation/cva6/issues/2116)

### Inferences
- The official 7-series frequency (50 MHz) was set in 2018. It has not been raised since, even though Thales later showed 100–140 MHz for 32-bit variants on the same Kintex-7 (Q4). It looks like a conservative "always closes" value for all configs, including 64-bit + FPU, rather than a measured Fmax.
- The official flow is not tuned for timing: retiming is on, but place/route use RuntimeOptimized and CI never checks WNS. So official frequencies say little about what the RTL can reach with a timing-driven flow.
- For our comparison: we close `cv64a6_imafdc_sv39` at 90.9 MHz on Zynq US+, about 1.8× the official 7-series target for the same config. The official project publishes no Fmax/WNS for this 64-bit config on any FPGA.

### Gaps
- I found no statement in the official README (checked at v4.0.0, v4.1.0, v4.2.0 and HEAD) that "Genesys2 runs at 50 MHz". The 50 MHz figure appears in the clock-generator script, the DTS/bootrom and maintainers' comments (#270, #608).
- I found no official UltraScale/UltraScale+ (VCU118, ZCU10x, KV260/KR260) build in the current flow, and no official frequency for one.
- The Thales CI dashboard (riscv-ci.pages.thales-invia.fr) was not examined. It may hold FPGA utilization history, but per the CI script no timing.

---

## Q2. What do the docs (user manual, README, CHANGELOG) and the code say about `FpgaEn`, `FpgaAlteraEn`, `cv32a6_ima_sv32_fpga` and other FPGA-optimized variants, and what gains are claimed?

### Takeaway
`FpgaEn` is a config bit, documented only as "Is FPGA optimization of CV32A6 (for Xilinx and Altera)". It moves some storage from flip-flops into FPGA RAMs:
- integer and FP register files into LUTRAM
- BTB and BHT into BRAM/LUTRAM
- several FIFOs into LUTRAM: instruction queue, write-through AXI adapter, write buffer, AMO buffer, accelerator dispatcher
- FPGA-inferred cache SRAMs

It does not touch the FPU, PMP, MMU/TLB logic or CSR file. On `master`, only `cv32a6_ima_sv32_fpga` enables it; `cv64a6_imafdc_sv39` has `FpgaEn = 0`. `FpgaAlteraEn` (2024) ports the same idea to Altera synchronous RAMs. The user manual has no FPGA timing guidance: its "FPGA specific guidelines" section is an empty placeholder. Gain claims come from conference papers (Q4), not the docs.

### Cited Findings
**Definition and documentation**
- `config_pkg.sv`: `// Is FPGA optimization of CV32A6 for Xilinx and Altera` → `bit FpgaEn;` and `// Is FPGA optimization for Altera FPGA` → `bit FpgaAlteraEn;` — [config_pkg.sv](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/core/include/config_pkg.sv)
- User manual parameter table: "`FpgaEn` | bit | Is FPGA optimization of CV32A6" — [user_cfg_doc.rst](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/docs/01_cva6_user/user_cfg_doc.rst) (rendered at docs.openhwgroup.org/projects/cva6-user-manual)
- User manual "FPGA specific guidelines" holds only suggested content: "Typical critical paths in FPGA and suggestions for optimizations" and "typical command lines / settings for various FPGA tools". Nothing is written — [Core_Integration.rst](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/docs/01_cva6_user/Core_Integration.rst)
- Requirements spec, PPA-10: "CVA6 should be resource-optimized on FPGA and ASIC targets". **PPA-30: "CV32A6 should run at more than 150 MHz in the cv32a6_imac_sv32 configuration on Kintex 7 FPGA technology, commercial -2 speed grade."** There is no FPGA frequency requirement for CV64A6; PPA-40 is ASIC: >900 MHz on 28FDSOI — [cva6_requirements_specification.rst](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/docs/02_cva6_requirements/cva6_requirements_specification.rst) (also at [cva6.readthedocs.io](https://cva6.readthedocs.io/en/latest/02_cva6_requirements/cva6_requirements_specification.html))
- The CHANGELOG has no `FpgaEn` entries. Its only FPGA-frequency entry is the 2019 "Reduce clock frequency of FPGA to 30 MHz to accomodate FPU" — [CHANGELOG.md](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/CHANGELOG.md)

**Where `FpgaEn`/`FpgaAlteraEn` act in RTL (grep of `core/` at HEAD)**
- `issue_read_operands.sv` uses `gen_fpga_regfile` / `gen_fpga_fp_regfile` when `FpgaEn`, i.e. `ariane_regfile_fpga.sv` (LUTRAM). `frontend/btb.sv` uses `gen_fpga_btb` and `frontend/bht.sv` uses `gen_asic_bht` only when `!FpgaEn`. `FpgaEn` is also passed as `FPGA_EN` to `cva6_fifo_v3` instances in `instr_queue.sv`, `wt_axi_adapter.sv` (8 uses), `wt_dcache_wbuffer.sv`, `std_cache_subsystem.sv`, `amo_buffer.sv`, `acc_dispatcher.sv` and `cva6.sv`. `FpgaAlteraEn` adds synchronous-RAM variants in `ariane_regfile_fpga.sv`, `bht.sv`, `cva6_fifo_v3.sv`, `id_stage.sv`, `issue_read_operands.sv` and `frontend.sv`. No FPU (cvfpu), PMP, MMU/TLB, CSR or scoreboard logic is conditioned on `FpgaEn` — [core/ tree @HEAD](https://github.com/openhwfoundation/cva6/tree/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/core)
- Which configs enable it: `cv32a6_ima_sv32_fpga_config_pkg.sv` has `FpgaEn: bit'(1)` and is the only `core/include` config with FpgaEn=1. `cv64a6_imafdc_sv39`, `cv64a6_imafdc_sv39_hpdcache`, `cv32a6_imac_sv32`, `cv32a60x` and `cv32a65x` all have `FpgaEn: bit'(0)` — [cv32a6_ima_sv32_fpga_config_pkg.sv](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/core/include/cv32a6_ima_sv32_fpga_config_pkg.sv), [cv64a6_imafdc_sv39_config_pkg.sv](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/core/include/cv64a6_imafdc_sv39_config_pkg.sv)
- `cv32a6_ima_sv32_fpga` contents:
  - XLEN 32, RVF = RVD = 0, ZiCond = 0
  - I$ 8 KiB 2-way and D$ 8 KiB 2-way, 128-bit lines, write-through D$
  - `NrScoreboardEntries = 4`, RAS 2, BTB 32, BHT 128, `NrLoadPipeRegs = 1`
  - `NrPMPEntries = 0`
  - Sv32 MMU with `InstrTlbEntries = 2`, `DataTlbEntries = 2`, `UseSharedTlb = 1`, `SharedTlbDepth = 64`

  By comparison, `cv64a6_imafdc_sv39` has scoreboard 8, I/D TLB 16/16 and no shared TLB — same files as above.
- Thales built these parameters in late 2022–2023 (Sébastien Jacq, Thales):
  - #989 "Fpga memories" (merged 2022-11-07)
  - #1000 "Config cache fpga"
  - #1002 "Scoreboard fpga parameter"
  - #1016 "add btb optimized for FPGA targets" ("predictable adresses are stored in BRAM for FPGA… Flushing is not supported for FPGA")
  - #1032 "Fifo v3 fpga 1" (LUTRAM FIFO)
  - #1038 "Regfile fpga", #1039 "Bht fpga"
  - #1052 TLB entries, #1062 PMP config, #1108 shared TLB, #1111 optional perf counters, #1130 WT D$ write-buffer size

  Source: [PR list by sjthales](https://github.com/openhwfoundation/cva6/pulls?q=author%3Asjthales), [PR #1016](https://github.com/openhwfoundation/cva6/pull/1016), [PR #993](https://github.com/openhwfoundation/cva6/pull/993)
- In #983 (2022-10-25) Jacq gives the rationale: "We are currently optimizing cv32a6 for FPGA targets… Our goal is for the CV32A6 to be independent of FPGA technology". He also says `tech_cells_generic`'s `tc_sram_xilinx` raised CV32A6 BRAM use "from 32 to 60". The parameter name `FPGA_EN` came from review by Jean-Roch Coulon (Thales) — [PR #983](https://github.com/openhwfoundation/cva6/pull/983)
- The earlier FPGA register file (Noam Gallmann, "ganoam", PR #497, merged 2020-08-24) uses distributed RAM for the integer and FP register files. On Kintex-7 xc7k325tffg900-2: LUT 40,499 → 36,350 (−10.2%), FF 22,799 → 18,806 (−17.5%), +440 LUTRAM. Whole design, configuration not stated, apparently the 64-bit SoC of that time — [PR #497](https://github.com/openhwfoundation/cva6/pull/497)
- Altera work (Angela Gonzalez Mariño, PlanV, Nov 2024):
  - #2590 adds the `CVA6ConfigFpgaAltera` parameter, renamed `FpgaAlteraEn` in review: "CVA6ConfigFpgaEn =1; // for Xilinx and Altera / CVA6ConfigFpgaAlteraEn =1; // for Altera (only)"
  - #2592 "Altera opt 1": instruction queue and WT AXI adapter FIFOs moved to synchronous LUTRAM, "because… asynchronous RAM primitives are used [for Xilinx], and Altera does not support asynchronous RAM"
  - #2602 "Altera opt 2": BHT to synchronous RAM
  - #2613 "Altera opt 3": register file to synchronous RAM, with the read address advanced one cycle via new `issue_entry_o_prev`/`issue_instr_i_prev` ports
  - Coulon noted the ASIC netlist grew 1.2 kgates until the new registers were gated by the parameter

  Source: [PR #2590](https://github.com/openhwfoundation/cva6/pull/2590), [PR #2592](https://github.com/openhwfoundation/cva6/pull/2592), [PR #2602](https://github.com/openhwfoundation/cva6/pull/2602), [PR #2613](https://github.com/openhwfoundation/cva6/pull/2613)
- FpgaEn bug fix: PR #2521 (FriedDede, 2024-10-01), "Fixed a multiple driver error in the branch target buffer, when CVA6.FpgaEn == 1" — [PR #2521](https://github.com/openhwfoundation/cva6/pull/2521)
- Third-party data point on the 64-bit config with FpgaEn. PR #2581 (Arty-A7 100T, WorldofJARcraft, closed unmerged 2025-02-13):
  - CVA6 runs at 25 MHz; "Design meets timing for cv32a6_imac_sv32 @ 25 MHz"
  - "A cv64imafdc_fpga configuration, in which I have enabled `CVA6ConfigFpgaEn`, i.e., inferring memories as block RAM, meets timing and fits the board with appx. 5000 LUTs to spare"
  - "Full cv64a6_imafdc_sv39 config (i.e., *without* `CVA6ConfigFpgaEn`) does not fit the board, uses appx. 1000 LUTs too much"

  Source: [PR #2581](https://github.com/openhwfoundation/cva6/pull/2581)

**New target structure (open PR, not merged as of 2026-10-27)**
- PR #3675 (yanicasa, 2026-10-27, against `master_candidate`) defines an "FPGA" group with `fpga_linux_cv32a6` and `fpga_linux_cv64a6`, "Maintained by PlanV. Reference images that boot Linux on the Genesys 2 board (cv64a6 is also built for Agilex 7)". `fpga_linux_cv32a6` "is the former cv32a6_imac_sv32 with FpgaEn set". `fpga_linux_cv64a6` "is the former cv64a6_imafdc_sv39_hpdcache_pmp_mmu_axi". "They are kept apart so that the parameters the board depends on (FPGA RAMs, cache sizes for timing) evolve with the board" — [PR #3675](https://github.com/openhwfoundation/cva6/pull/3675)
- In that PR, `config/target/fpga_linux_cv64a6/rtl_cfg_pkg.sv` sets `FpgaEn: bit'(1)`, `FpgaAlteraEn: bit'(0)`, RVF = RVD = 1, RVB = 1, `NrScoreboardEntries 8`, BTB 32, `PH_BHT` 128, `NrPMPEntries 8`, I$ 16 KiB 4-way, D$ 32 KiB 8-way, ITLB/DTLB 16/16, no shared TLB, AXI4-ATOP NoC. `doc.yml` role: "Reference 64-bit configuration to boot Linux on the Genesys 2 board, also built for the Agilex 7 board: rv64gc with B, Sv39, S and U, PMP, CVXIF, FPGA RAMs." — [PR #3675 head 398b80c8, fpga_linux_cv64a6](https://github.com/yanicasa/cva6/tree/398b80c85987337268c44b8da659ae1ed87b92f6/config/target/fpga_linux_cv64a6)

**Gain claims (from papers, details in Q4)**
- Thales (Kintex-7 XC7K325T-2, CV32A6 with MMU and L1 caches): LUT −55%, FF −61%, BRAM −67%, Fmax 100 → 140 MHz (+40%) — [Jacq et al., RISC-V Summit Europe 2023](https://riscv-europe.org/summit/2023/media/proceedings/posters/2023-06-07-J%C3%A9r%C3%B4me-QU%C3%89VREMONT-abstract.pdf)
- PlanV/Thales (Agilex 7): enabling the Altera FPGA optimizations gave FF −34%, LUT −7%, BRAM +33%, Fmax 200 → 215 MHz — [Gonzalez et al., RISC-V Summit Europe 2025](https://riscv-europe.org/summit/2025/media/proceedings/2025-05-15-RISC-V-Summit-Europe-P3.1.02-GONZALEZ-abstract.pdf)

### Inferences
- The +40% Fmax claimed for "FPGA optimizations" (Thales 2023) is for a 32-bit core. It bundles the `FpgaEn` RAM mapping with configuration reductions (scoreboard 4, 2-entry L1 TLBs plus a shared SRAM TLB, small caches, no FPU/PMP) and with "breaking critical timing paths". It should not be read as the effect of `FpgaEn = 1` alone on a 64-bit RV64GC config.
- `FpgaEn` leaves alone the modules that third parties report as critical in 64-bit + D builds (FPU/fpnew FMA, MMU, PMP, scoreboard/controller; see Q3). Setting `FpgaEn = 1` on `cv64a6_imafdc_sv39` would mostly save LUT/FF; any Fmax gain is likely modest. PlanV measured only +7.5% from the RAM mapping on Agilex, for 32-bit.
- The upcoming official 64-bit FPGA reference (`fpga_linux_cv64a6`) is close to our setup: RV64GC, 8 PMP, 16/16 TLB, 32 KiB 8-way D$. The differences are `FpgaEn = 1`, HPDcache instead of WT, and B and CVXIF enabled. The project apparently intends to keep a 64-bit FPGA config with FpgaEn on.

### Gaps
- No official document quantifies `FpgaEn` alone for a 64-bit config, on any FPGA family.
- I did not find official text explaining how `cv32a6_ima_sv32_fpga` differs from `cv32a6_imac_sv32` beyond the code. The CHANGELOG and README are silent.
- I did not check whether `cv32a6_ima_sv32_fpga` will survive in PR #3675's 35-target set. The PR says the 48 other targets are removed.

---

## Q3. GitHub issues, PRs and discussions about FPGA timing failures, critical paths, negative slack, and attempts at 100 MHz or more

### Takeaway
The maintainers' line has been consistent:
- ~50 MHz (Virtex-7, 2018) and ~60 MHz (Kintex-7, 2019) are realistic on 7-series; "100 MHz is a bit too tight, even without FPU" on Kintex-7.
- Vivado retiming of the FPU pipeline is weak, and "100 MHz should be possible on UltraScale+" (Zaruba, 2021).
- An early estimate was ~150 MHz on Virtex UltraScale+ SG2 (Schaffner, 2018).

Users report:
- 64-bit on Kintex UltraScale+ KU5P works at 100 MHz with Linux but fails badly at 200 MHz.
- Artix-7 at 100 MHz fails mostly in the FPU.
- Nexys Video (Artix-7 -1) needs 25 MHz.

The recurring critical paths are the FPU (fpnew FMA; fixed by out-of-context synthesis with retiming), the MMU (noted by Coulon on Genesys2), the scoreboard/controller (PlanV 2026), RVFI/trace logic (Capabilities) and JTAG CDC paths when raising the clock. No official answer gives a maximum frequency for 64-bit configs.

### Cited Findings
**Maintainer statements (ETH/PULP era)**
- #77 (lvcargnini, 2018-08-20, xcvu9p, target ≥200 MHz, "barrage of timing issues").
  - Zaruba: "I do remember that I was closing timing at approximately 50 MHz on a Virtex 7."
  - Schaffner (2018-08-30): "In terms of operating frequency, I expect the Ariane design to close around 150MHz on a Virtex UltraScale+ device (SG2)". The asynchronous-reset impact is "usually quite small (~4% slower, <0.5% more logic…)".

  Source: [issue #77](https://github.com/openhwfoundation/cva6/issues/77)
- #226 (hyf6661669, 2019-04-25, Genesys2 XC7K325T-2, Vivado 2018.2, asks whether Vivado can retime `fpnew_pipe_out` registers at 100 MHz).
  - Schaffner: "so far we could not really get it working well with the Vivado FPGA flow… the complete mapping runs around 60MHz on a Kintex-7 (Genesys2). 100MHz is a bit too tight, even without FPU."
  - Schaffner again: "previously we had to lower to 30MHz with FPU enabled".
  - Zaruba (2021-07-19): "the retiming in Vivado is still quite weak compared to Synopsys. The FPU now has a version with naïvely distributed registers which should perform a bit better on the FPGA. 100 MHz should be possible on Ultrascale+ devices."
  - Schaffner's PR #224 "Fpu piped" ("improves the timing of the FPU on FPGA mappings", 2019-04-25) was closed unmerged on GitHub.

  Source: [issue #226](https://github.com/openhwfoundation/cva6/issues/226), [PR #224](https://github.com/openhwfoundation/cva6/pull/224)
- #283 (2019-07-17), on Fmax/utilization data for Genesys2. Zaruba: "You get utilization and timing reports when running the implementation. A nice table for the readme would be welcome as a PR." No table was ever added — [issue #283](https://github.com/openhwfoundation/cva6/issues/283)
- #270 (jrrk, 2019-08-23): "The Ariane repository takes advantage of this [AXI channel independence] to improve timing on the FPGA by adding extra delay cycles compared with Verilator" — [issue #270](https://github.com/openhwfoundation/cva6/issues/270)

**User reports with numbers**
- Nexys Video PR #350 (xushengj, 2019-11-16, XC7A200T-1): "Vanilla ariane core has a critical path delay of about 24-26 ns along FPU datapath on XC7A200T, and adding latency to FPU moves the critical path to integer data path with delay of about 23 ns." That gave a 40 MHz clock, later 25 MHz: "We get timing violations when targeting 50MHz" (2022). The Ethernet module also "keeps having timing violations" — [PR #350](https://github.com/openhwfoundation/cva6/pull/350)
- #976 (0ena, 2022-10-12, Genesys2, Vivado 2019.2): moving 50 → 53 MHz gave "big SETUP violations on the dmi_jtag module, between clocks tck and clk_out1". Example: `Slack (VIOLATED) : -5.130ns`, 0.125 ns requirement, clock path skew −4.060 ns. The user's fix: "relaxed the maximum delays in the .xdc file of the failing dmi_jtag paths" and updated `cv64a6.dts`/`ariane.dts`; "runs without issues so far". Today's `ariane.xdc` has `set_max_delay -datapath_only … 20.000` on these CDC paths — [issue #976](https://github.com/openhwfoundation/cva6/issues/976), [ariane.xdc](https://github.com/openhwfoundation/cva6/blob/742dc82a0c706e0a3bfb98b709fd3ee06d50d12a/corev_apu/fpga/constraints/ariane.xdc)
- #1749 (chenqian13, 2024-01-06, Xilinx KU5P, Kintex UltraScale+).
  - chenqian13: "I increased the main frequency of CVA6 to 100MHz… Except for some garbled serial output when starting the Linux system… everything else runs well. But when I increased the main frequency of CVA6 to 200MHz, there was a significant clock violation in the VIVADO project, and the Linux system could not start". Later: "After I changed CLK_OUT1=100MHz… Vivado did not report any errors". The DTS for the bootrom and SDK was updated. Related #1778 says the system is "cva6-sdk on xcku5p" with CLK_OUT1 = 100 MHz.
  - demofpga (2024-01-28), Artix-7 A100T -2 at 100 MHz: "significant clock violation… question was forcus on the FPU" (timing reports attached as zip).
  - Maintainers: Coulon: "The max frequency uses to be higher on ASIC than FPGA… @sjthales knows the max frequency we can reach on FPGA." Sébastien Jacq never answered with a number. Quévremont pointed to the 2023 Summit poster: "Contributions are welcome to extend the analysis of performance on FPGA." The issue was auto-closed for inactivity.

  Source: [issue #1749](https://github.com/openhwfoundation/cva6/issues/1749), [issue #1778](https://github.com/openhwfoundation/cva6/issues/1778)
- #2895 (maxicraft0, 2025-04-02, Virtex-7 XC7VX485T, config with F and D, 2 ns constraint): "nearly -15ns of slack for setup time". It identifies a long datapath in `core/cvfpu/src/fpnew_fma.sv`: the 53-bit mantissa product.
  - Fix by maxicraft0 (2025-09-27): "pre-synthesize fpnew_fma module with -retiming -mode out_of_context option (there are pipeline registers inside the fpnew_fma module however they are not evenly populated within the module so we need -retiming). Then use the pre-synthesized netlist".
  - koni-ey (2025-10-01) confirmed it "fixed my problems": a new FPU wrapper, synthesized OOC with `-retiming`, DCP imported.
  - No maintainer replied.

  Source: [issue #2895](https://github.com/openhwfoundation/cva6/issues/2895)
- #2700 (MikeOpenHWGroup, 2025-01-10, open): "OpenPiton configuration of CVA6 cannot boot Linux on UltraScale+ FPGA".
  - Jbalkind: "we only observed this issue on UltraScale+ FPGAs… I think there's a specific timing component to the issue".
  - Meeting notes 2025-01-15 (jquevremont): "@JeanRochCoulon mentions that MMU was often in the critical path of the Genesys 2 board and recommends reviewing Vivado's logs."
  - Still unresolved as of Nov 2025.

  Source: [issue #2700](https://github.com/openhwfoundation/cva6/issues/2700)
- #3241 (PRugg-Cap, Capabilities Ltd., 2026-03-18): RVFI is "showing up in timing paths" in their FPGA builds, so they disabled it in their fork — [issue #3241](https://github.com/openhwfoundation/cva6/issues/3241)
- Thales task #987 "Submit CVA6 FPGA optimizations" (Quévremont, 2022-10-28 to 2024-05-28) listed "FPGA memory, Front end optimization, TLB optimization, Cache size optimization, Scoreboard sizing, Regfile optimization". 2023-03-14: "Focus on frequency optimization in 2023 (mainly targetting FPGA)". 2023-04-18: "1 merged PR to investigate (#1130): timing analysis. 1 upcoming PR (critical path in division)". 2024-05-28: "Deferring future FPGA optimizations to a new task." — [issue #987](https://github.com/openhwfoundation/cva6/issues/987)
- GitHub Discussions: only 4 FPGA hits (#3003 ILA, #1732 bare-metal, #1025 UART, #787 "Targeting Other FPGA Boards" for Alveo U280). None covers timing or frequency — [discussions](https://github.com/openhwfoundation/cva6/discussions)

**ASIC-side critical-path reports (same RTL, not FPGA, for context)**
- #3104 (Ly-Van-Minh, 2025-09-30, `cv64a6_imafdc_sv39` v5.3.0, DC 14 nm at 2 ns): "Many violate REG2OUT, IN2REG, REG2REG paths". In the same thread, 0rd1narY1 (TSMC28, 0.8 ns): "too many long paths (>1ns) in pmp, fpnew, csr_regfile" — [issue #3104](https://github.com/openhwfoundation/cva6/issues/3104)
- #3117 (open): DC retiming not applied to `fpnew_fma`. Ly-Van-Minh: "the violations of LSU and FPU are still there", some `*pipe_reg*` not moved — [issue #3117](https://github.com/openhwfoundation/cva6/issues/3117)
- PR #3341 (César Fuguet, merged 2026-06-13): "Recent ASIC synthesis with the CVA6+HPDcache exhibit a critical path concerning the response path for AMOs… adds a pipeline buffer… increases the latency of AMOs by one cycle" — [PR #3341](https://github.com/openhwfoundation/cva6/pull/3341)

### Inferences
- In every report with a double-precision FPU (#226, #350, #1749-demofpga, #2895), the FPU/fpnew FMA dominates the 7-series critical path. The documented community fix is OOC synthesis of `fpnew_fma` with retiming (#2895). This matches our case: unmodified `cv64a6_imafdc_sv39` with D, closing at 90.9 MHz but not 100 MHz on Zynq US+. The FPU, MMU/PMP, scoreboard/issue and RVFI/trace logic are the first places to look in our critical-path report.
- #1749's "100 MHz works on KU5P" is the closest third-party data point to our UltraScale+ case, but it has no WNS, config or speed grade. The KU5P on the kit is probably -2 (an inference; not stated). It also says nothing of how it closed (a default `make fpga` flow with RuntimeOptimized P&R would be the natural assumption). Treat it as anecdotal.
- At a 2 ns target, a −15 ns slack (#2895) means a path of about 17 ns, roughly 59 MHz, on Virtex-7 -2 before the OOC retiming fix. This lines up with the maintainers' 50–60 MHz guidance for 7-series. (My arithmetic, not stated in the issue.)
- The DONT_TOUCH on `i_cva6_rvfi`, `i_iti` and `i_encapsulator` in the official `ariane.xdc` keeps trace logic in the FPGA netlist, consistent with #3241's report that RVFI appears in timing paths. (Inference: I did not measure it.)

### Gaps
- No maintainer ever gave an official Fmax for a 64-bit config on any FPGA. The question in #1749 (2024) was left unanswered.
- I could not open demofpga's attached timing report zip (#1749) to extract the slack values.
- I found no official discussion of PMP-specific critical paths on FPGA. PMP shows up only in the ASIC reports (#3104).
- OpenHW TWG/CVA6 meeting minutes outside GitHub were not found or searched in depth. Only the 2025-01-15 meeting summary in #2700 was seen.

---

## Q4. Published FPGA results (frequency, resources) from OpenHW, Thales, PlanV, 10xEngineers and others for CVA6 variants, including Fmax gains from FPGA-specific RTL changes

### Takeaway
All official or semi-official published FPGA Fmax numbers are for **32-bit, FPU-less** CV32A6 variants:

| Source | FPGA | Result |
|---|---|---|
| Thales 2023 | Kintex-7 -2 | 100 MHz originally → **140 MHz** after FPGA optimizations, with LUT −55%, FF −61% |
| Thales 2023 slides | Zynq UltraScale+ -3 | **125 MHz** (RV32IMA, 8K+8K caches, MMU, no FPU) |
| PlanV/Thales 2025 | Agilex 7 | **200–220 MHz** |
| PlanV 2026 | Xilinx | scoreboard/controller restructuring gives **+14% Fmax** on the OpenHW FPGA config |

No official Fmax has been published for any 64-bit/FPU configuration. The only official 64-bit data points are operating frequencies: 50 MHz on Genesys2 and 100 MHz on Agilex 7 (reduced from 200 MHz because of 64-bit timing problems). I found no FPGA timing results from 10xEngineers.

### Cited Findings
**Thales Research & Technology, RISC-V Summit Europe 2023 (Barcelona, 5–9 June 2023)**
- Jacq, Coulon, Eyssartier, Quévremont, "Recent Achievements of the Open-Source CVA6 Core: FPGA Optimizations, Coprocessor Acceleration, Yocto Linux Support". The summary says the FPGA optimizations "reduce by 55% the resources while increasing performance by 40%". Table 1, "Key performance indicators of CVA6, including MMU and L1 caches on Xilinx Kintex 7 FPGA (XC7K325T-2)", Original CV32A6 → Optimized version:

  | Metric | Original CV32A6 | Optimized version | Change |
  |---|---|---|---|
  | LUTs | 18,103 | 8,077 | −55% |
  | Flip-flops | 11,484 | 4,403 | −61% |
  | DSP | 4 | 4 | — |
  | BRAM | 36 | 12 | −67% |
  | **Max. freq.** | **100 MHz** | **140 MHz** | **+40%** |
  | CoreMark/MHz | 2.8 | 2.8 | — |
  | CoreMark | 280 | 392 | — |

  - The first set of optimizations reduced resources through "the RV32C decoder, the branch prediction unit, the instruction and data caches, the register file, the performance counters, the scoreboard, or the memory management unit (MMU)". The MMU gained "a second level of [TLBs] implemented in SRAM to reduce the size of the first level… implemented with flip-flops".
  - "The second set of optimizations has increased the processor frequency by breaking critical timing paths."

  Source: [Jacq et al. 2023 extended abstract (PDF)](https://riscv-europe.org/summit/2023/media/proceedings/posters/2023-06-07-J%C3%A9r%C3%B4me-QU%C3%89VREMONT-abstract.pdf)
- Thierry Collette (Thales), plenary slides "4 years of Open Source RISC-V at Thales", 2023-06-08.
  - Slide "HW implementations", CV32A6 FPGA: "Frequency 125 MHz; Performance 2.25 CoreMark/MHz, 281 CoreMark; Resources 10,416 LUT, 6,313 FF, 10 BRAM, 4 DSP; Technology Zynq UltraScale+ -3; Configuration RV32IMA, 8K D$ + 8K I$, noFPU, MMU". For comparison, CV32A6 ASIC: 900 MHz, 2.5 CoreMark/MHz, 80 kgates, 28 nm worst case.
  - Slide "CVA6 2022 results: FPGA optimization" repeats the Kintex-7 table above (100 → 140 MHz, "Some optimizations are also beneficial for ASIC").
  - Roadmap slide: "2022 – Optimizations (+50% freq. and -30% area)". This conflicts with the +40% / −55% in the same deck and in the abstract; it is likely a different baseline.
  - Positioning: "For any FPGAs (32 bit)". 2020–2021 student contest "Improve CV32A6 FPGA performance" (winners: Télécom Paris, U. Toulouse III).

  Source: [Collette 2023 slides (PDF)](https://riscv-europe.org/summit/2023/media/proceedings/plenary/2023-06-08-09h30-Thierry-COLLETTE-slides.pdf)

**PlanV + Thales, RISC-V Summit Europe 2025 (Paris, 12–15 May 2025)**
- Gonzalez, Karadayi (PlanV), Jeulin, Biquard, Quévremont (Thales), "CVA6 Design Space Exploration on Agilex 7 FPGA".
  - It starts from "the existing FPGA configuration from OpenHW". The Xilinx-specific optimizations "can be enabled with a configuration flag (FpgaEn). However, they can't be reused [on Altera] because the FPGA fabric does not support the same primitives."
  - Porting them (Config B) "reduce[s] the number of Flip-Flops (FFs) by 34%, and the number of Look Up Tables (LUTs) by 7%, in exchange for a 33% of extra Block RAM… The overall performance (Coremark) improves slightly, because the maximum frequency achieved on the FPGA is a bit higher (thanks to the better routing in the FPGA when moving registers to memory)".
  - Table 2/3 results:

    | Config | Description | LUTs | FFs | BRAM | CoreMark/MHz | Fmax | CoreMark |
    |---|---|---|---|---|---|---|---|
    | A | OpenHW FPGA config w/o Xilinx optimizations | 12,530 | 8,959 | 24 | 2.00 | **200 MHz** | 400 |
    | B | Altera FPGA optimizations | 11,621 | 5,874 | 32 | 2.00 | **215 MHz** | 430 |
    | C | No MMU | 11,411 | 7,908 | 20 | — | 215 MHz | — |
    | D | Best cache (16 KB, 512-bit line, 4-way) | 15,773 | 7,521 | 135 | 2.30 | 215 MHz | 498 |
    | E/F/G | Further reductions | — | — | — | — | 217–220 MHz | — |
    | H, I, J | Reduced cache / 2 SB entries / 1 load buffer | — | — | — | — | 220 MHz | — |
    | K | SRAM instead of DDR | — | — | — | — | 210 MHz | 378 |
    | L | H + SRAM instead of DDR | 7,710 | 4,422 | 16 | 2.5 | 210 MHz | 525 (+31%) |

  - Config A is described as "OpenHW FPGA config. w/o Xilinx optimizations".

  Source: [Gonzalez et al. 2025 extended abstract (PDF)](https://riscv-europe.org/summit/2025/media/proceedings/2025-05-15-RISC-V-Summit-Europe-P3.1.02-GONZALEZ-abstract.pdf), [poster listing](https://riscv-europe.org/summit/2025/posters)

**PlanV, RISC-V Summit Europe 2026 (poster #YXSRKX, Wednesday 10)**
- Udaya Raj Subedi and Angela Gonzalez, "CVA6 Optimization". The abstract says analysis "showed that the scoreboard (SB) and controller are the biggest combinational modules involved in the critical path". It proposes "re-order buffer (ROB) and Issue logic separation from the Scoreboard and registering Controller output", and "we get to improve the maximum frequency of operation by 14% for the existing FPGA configuration from OpenHW for Xilinx FPGA". The abstract gives no absolute MHz, device or config — [RISC-V Summit Europe 2026 posters](https://riscv-europe.org/summit/2026/posters)

**ETH/PULP and others**
- Noam Gallmann's FPGA register file (PR #497, 2020): Kintex-7 LUT −10.2%, FF −17.5%. Frequency not reported — [PR #497](https://github.com/openhwfoundation/cva6/pull/497)
- CVA6S+ (Tedeschi et al., UniBo/ETH/ST/Inria, RISC-V Summit Europe 2025 / arXiv 2505.03762):
  - Implemented on Genesys 2 Kintex-7 in the Cheshire SoC (32-bit, 32 KiB 8-way D$, 16 KiB 4-way I$).
  - An optional Load Unit output register was used "to improve timing closure".
  - No FPGA frequency is reported. The 13.5% Fmax boost and the "<0.5%" degradation figures are ASIC (GF22) numbers. A search-engine summary that attributed the 13.5% to Genesys 2 was wrong.

  Source: [arXiv 2505.03762v2](https://arxiv.org/html/2505.03762v2)
- 10xEngineers: in #2700, `cv32a6_imac_sv32` is called "the 10xEngineers configuration", and 10xEngineers offered to debug the UltraScale+ Linux hang. I found no FPGA frequency/resource publication from them — [issue #2700](https://github.com/openhwfoundation/cva6/issues/2700)
- A search result reported that a CVA6-CHERI variant (Capabilities Ltd/Cambridge, CHERITech'25 slides) reached 50 MHz on Genesys II versus 41 MHz before. The PDF URL returned 404 when fetched, so this is **unverified** — [search result: CHERITech25 slides](https://cheri-alliance.org/wp-content/uploads/2025/11/2.1-Jonathan-Woodruff-CHERITech25.pdf)

### Inferences
- **7-series vs UltraScale+ vs Intel:**
  - 7-series (Kintex-7 -2): official operating point 50 MHz; Thales Fmax 100 MHz for the original CV32A6 and 140 MHz optimized (32-bit, no FPU).
  - Zynq UltraScale+ -3: Thales 125 MHz (32-bit, no FPU). Whether this build had the 2022 optimizations is not stated. The 10,416 LUTs fall between the "original" 18,103 and "optimized" 8,077 Kintex-7 counts, which suggests a different config or tool flow.
  - Agilex 7: 200–220 MHz Fmax (32-bit); official APU at 100 MHz for both XLENs after 64-bit timing trouble at 200 MHz.
- The Zynq US+ -3 figure is the closest official reference to our KR260 (xck26, -2LV). A -2LV part is slower than -3, and our core is 64-bit with a D-capable FPU, 8 PMP entries and 16/16 TLBs. Under those conditions our 90.9 MHz closure looks plausible next to Thales's 125 MHz for a much smaller 32-bit core. This is an inference by analogy, not an official benchmark.
- The official project has never published a 64-bit FPGA Fmax. The Agilex note ("Reduce the frequency of operation to 100MHz to avoid timing issues in 64bit version", while 32-bit designs reach ~200–220 MHz there) shows that the 64-bit/FPU configuration is roughly half as fast as the 32-bit FPGA config even on a modern FPGA.

### Gaps
- No published Fmax/WNS for `cv64a6_imafdc_sv39` (or any 64-bit CVA6) on any FPGA from OpenHW, Thales, PlanV or 10xEngineers.
- The absolute frequencies behind PlanV's 2026 "+14%" result are unavailable: the poster page shows only the abstract and no PDF was linked.
- The exact baseline of Thales's "+50% freq. and −30% area" roadmap claim (versus the +40% / −55% table) is not explained in the slides.
- The CVA6-CHERI 41 → 50 MHz Genesys II figure could not be verified because the slides returned 404.
