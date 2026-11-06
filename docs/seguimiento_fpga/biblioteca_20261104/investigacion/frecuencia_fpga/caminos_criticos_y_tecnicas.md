# CVA6/Ariane (and FPnew/cvfpu) on FPGA: critical paths, frequency-raising techniques, and methodology checks

Scope note: research done 2026-10-27. Facts marked "(local)" were verified by reading the team's checkout at `/home/nachofalchi/data/fpga-work/cva6-equipo` (`git describe`: `v5.3.0-319-gdf6b051`). For those, the link points to the same path in upstream `openhwgroup/cva6` (or `openhwgroup/cvfpu`); upstream master may have moved since, so the local file is the authority. Device-family flags: **[7-series]**, **[ASIC]**, **[Zynq-7000]**, **[US+]**.

## Q1. Which CVA6 paths are reported as FPGA-critical, and is the FPU (conversion/FMA) or PMP path a known limiter?

### Takeaway
The only CVA6 path with public FPGA reports is the FPU, specifically the `fpnew_fma` mantissa-product datapath. The reported fix is to run retiming on the FPU in an out-of-context (OOC) synthesis. I found no public FPGA report that names the PMP NAPOT path or the conversion-unit path. PMP shows up only in an ASIC report. CVA6's own FPGA flow runs the core at 50 MHz on 7-series boards, so upstream has never had to close 100 MHz with the 64-bit FD configuration. Our 90.9 MHz on a -2LV (0.72 V) UltraScale+ part is at or above every public data point I found.

### Cited Findings
**FPU / FMA (FPGA)**
- Issue #2895, "FPGA synthesis: Long data path inside the FPU module" (opened 2025-04-02, closed as not planned 2025-05-11) **[7-series]**:
  - Setup: XC7VX485T (Virtex-7), Vivado, CVA6 with F/D, clock "2 ns" (500 MHz, an unrealistic target).
  - Result: "nearly -15ns of slack". The worst path is at the product assignment in `core/cvfpu/src/fpnew_fma.sv`, with a 53-bit mantissa (FP64).
  - Maintainers gave no technical reply. — [openhwgroup/cva6#2895](https://github.com/openhwgroup/cva6/issues/2895)
- Community workaround in the same thread:
  - maxicraft0 (2025-09-27): pre-synthesize `fpnew_fma` with `-retiming -mode out_of_context`, because "the pipeline registers inside the module are unevenly placed". Then use the resulting netlist in the full project.
  - koni-ey (2025-10-01): confirmed it fixed their timing. They wrapped the FPU, synthesized it with the same options, and imported the DCP.
  - Ly-Van-Minh (2025-10-23): when the FPU was not synthesized separately, the `inp_pipe_*`, `mid_pipe_*`, `out_pipe_*` registers were **not moved**. They also pointed at `shift_reg` in `load_store_unit.sv`.
  - Source: [openhwgroup/cva6#2895](https://github.com/openhwgroup/cva6/issues/2895)
- Issue #1749, "How high the main frequency can CVA6 run on FPGA?" (Jan–Mar 2024):
  - chenqian13, KU5P (Kintex UltraScale+): 100 MHz "runs well" (Linux, after fixing UART divisor and DTS). 200 MHz gave a "significant clock violation" and Linux did not boot.
  - demofpga, Artix-A100T -2 **[7-series]**: at 100 MHz, "significant clock violation" with the "focus on the FPU".
  - The thread has no WNS or path data. — [openhwgroup/cva6#1749](https://github.com/openhwgroup/cva6/issues/1749)
- In #1749, JeanRochCoulon (maintainer, 2024-01-07) wrote: "The max frequency uses to be higher on ASIC than FPGA, and that is the case with CVA6." jquevremont pointed to an FPGA performance poster from RISC-V Europe 2023 and said "Contributions are welcome to extend the analysis of performance on FPGA." — [openhwgroup/cva6#1749](https://github.com/openhwgroup/cva6/issues/1749)

**Historical data points**
- Issue #77 (Aug 2018, Ariane era):
  - zarubaf recalled closing timing at "approximately 50 MHz on a Virtex 7" **[7-series]**.
  - msfschaffner *expected* (not measured) "around 150MHz" on Virtex UltraScale+ SG2. He estimated the async reset costs "~4% slower, <0.5% more logic".
  - The issue does not say whether that 2018 core had an FPU. — [pulp-platform/ariane#77](https://github.com/pulp-platform/ariane/issues/77)
- The CVA6 user manual (2023) states a PPA *target*, not a measurement: CV32A6 `cv32a6_imac_sv32` (32-bit, no FPU) >150 MHz on Kintex-7 -2 **[7-series]**. It also says the branch unit is on the critical path and the LSU is timing-sensitive because it interfaces the SRAMs. This comes from a search-engine extract of the PDF; I did not open the full document. — [CVA6 user manual PDF](https://docs.openhwgroup.org/_/downloads/cva6-user-manual/en/cv32a6_v0.1.0/pdf/)
- The TelmoFieux CVA6 out-of-order fork reports "Original CVA6" Fmax = **49.7 MHz** from OOC place-and-route of CV32A6 on a Zybo Z7-20 (Zynq-7020) **[7-series]**. Its OoO variants reach 42.2–53.2 MHz. — [TelmoFieux/cva6-Out-of-Order](https://github.com/TelmoFieux/cva6-Out-of-Order)

**Upstream FPGA flow (local)**
- Clock: the clock generator sets `CLKOUT1_REQUESTED_OUT_FREQ {50}` (core clock 50 MHz) for Genesys2/VC707/VCU118/KC705, and 25 MHz for Nexys Video. — [xlnx_clk_gen/tcl/run.tcl](https://github.com/openhwgroup/cva6/blob/master/corev_apu/fpga/xilinx/xlnx_clk_gen/tcl/run.tcl), [ariane_xilinx.sv](https://github.com/openhwgroup/cva6/blob/master/corev_apu/fpga/src/ariane_xilinx.sv) (local)
- Flow: the upstream `run.tcl` sets `STEPS.SYNTH_DESIGN.ARGS.RETIMING true` and uses `RuntimeOptimized` place and route directives. It is not a performance-oriented flow. — [corev_apu/fpga/scripts/run.tcl](https://github.com/openhwgroup/cva6/blob/master/corev_apu/fpga/scripts/run.tcl) (local, lines 85, 102–103)

**Other timing-related upstream changes**
- Release notes for CVA6 v4.2.0: "Improve FPU pipelining and timing around scoreboard", "Fix potentially long timing path in `axi_lite_interface`", "Bump `fpnew` to `v0.5.5`". No release note mentions FpgaEn, frequency or retiming. — [CVA6 releases](https://github.com/openhwgroup/cva6/releases)

**PMP (ASIC only)**
- Issue #3104 **[ASIC]**: `cv64a6_imafdc_sv39` v5.3.0 in Design Compiler, 14 nm, 2 ns period, "many long data paths". A follow-up (0rd1narY1, 2025-10-14) reports paths >1 ns in **pmp, fpnew and csr_regfile** for `cv64a6_imafdcv_sv39` at 28 nm with a 0.8 ns target. No fixes were posted. — [openhwgroup/cva6#3104](https://github.com/openhwgroup/cva6/issues/3104)

**General FPGA timing (not CVA6)**
- A 2025 paper on a 32-bit five-stage RISC-V core on a 20 nm FPGA finds that FPGA critical-path timing is "dominated by routing parasitics and placement dependent variability". The dominant path is EX→MEM. On ASIC the same path is governed by logic depth. — [arXiv 2512.13866](https://arxiv.org/abs/2512.13866)

**Device speed grade**
- The K26 SOM uses `XCK26-SFVC784-2LV-C/I`. AMD defines "-2LV" as a -2L device operated at VCCINT = 0.72 V. At 0.72 V the -2LE/-1LI parts have reduced performance compared with 0.85 V. I did not find an exact derating figure for the K26. — [K26 SOM datasheet (mirror)](https://www.sundance.com/wp-content/uploads/docs/k26-som-Data-Sheet.pdf), [DS923 Speed Grade Designations](https://docs.amd.com/r/en-US/ds923-virtex-ultrascale-plus/Speed-Grade-Designations), [DS925 speed grades/voltages](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/Available-Speed-Grades-and-Operating-Voltages)

### Inferences
- **Our failing conversion path is explained by the FPU RTL; it is not a random routing artifact** (see Q2).
  - With `PipeConfig = DISTRIBUTED` and `LAT_CONV = 2`, `fpnew_cast_multi` gets 1 input register, 1 middle register and **0 output registers**.
  - So the path starts at the cast unit's internal (middle) register and runs through the second half of the cast datapath and the combinational output arbiters in `fpnew_opgroup_block` and `fpnew_top` (`rr_arb_tree`).
  - It then continues through `fpu_wrap` and `ex_stage` (`fpu_result_o`/`fpu_trans_id_o` are plain `assign`s) into the scoreboard and operand forwarding.
  - The same applies to the FP32 FMA (`LAT_COMP_FP32 = 2` → no output register) and NONCOMP (`LAT_NONCOMP = 1` → no output register).
- **Our numbers, for scale:** WNS −0.553 ns at 10 ns corresponds to about 94.8 MHz for that run (1 / 10.553 ns). Upstream runs at 50 MHz on 7-series. The only comparable US+ report is the KU5P one: 100 MHz "works", with no WNS given. KU5P parts are usually -2 at 0.85 V, which is faster than our -2LV, so a full 64-bit F/D CVA6 at 90–95 MHz on a K26 is plausible as the ceiling without RTL or configuration changes. The KU5P comparison is not like-for-like.
- **The FMA problem in #2895 matches our "`fpnew_fma` internal" path.** The FP64 FMA (3 registers → in/mid/out = 1/1/1) is internally unbalanced, and Vivado only rebalances it if retiming actually runs on it (see Q5).
- **PMP being critical on our build is plausible.** It is consistent with the ASIC report (#3104) and with the RTL structure (Q3), but I found no FPGA-specific public confirmation.

### Gaps
- No public post-route Vivado report with logic levels for 64-bit CVA6 (`cv64a6_imafdc_sv39`) on any FPGA.
- I could not find the Thales "RISC-V Europe 2023" FPGA performance poster cited in #1749.
- The demofpga timing reports in #1749 are in an attached zip whose contents are not visible on the page.
- No public FPGA report names the D-cache write buffer, TLB→I-cache or operands→LSU paths. The user manual's statements that the "LSU is timing-sensitive" and "the branch unit is on the critical path" are the only related public text, and they come from a search extract.

## Q2. FPnew/cvfpu: recommended pipeline configuration for FPGA; documented effects of changing PipeRegs/PipeConfig

### Takeaway
cvfpu gives no FPGA-specific recommendation. Its documentation says registers are pre-placed and "strongly" encourages automatic retiming in synthesis to balance them. CVA6 hard-codes `DISTRIBUTED` and latencies in `ariane_pkg.sv`. With 2 stages, DISTRIBUTED puts no register at the unit's output, which is why the conversion path reaches the scoreboard. I found no published sweep of PipeRegs/PipeConfig against FPGA frequency. The only FPGA "result" is qualitative: OOC retiming of the FMA "fixed" timing in #2895.

### Cited Findings
**cvfpu documentation**
- PipeRegs: "This parameter sets a number of pipeline stages to be inserted into the computational units per operation group, per FP format." The default is `'{default: 0}` (fully combinational). — [cvfpu docs/README.md](https://github.com/openhwgroup/cvfpu/blob/develop/docs/README.md)
- PipeConfig: "The requested number of registers is placed to predefined locations within the units according to the PipeConfig parameter" and "For best results, we _strongly_ encourage the use of automatic retiming options in synthesis tools to optimize the pre-placed pipeline registers." — [cvfpu docs/README.md](https://github.com/openhwgroup/cvfpu/blob/develop/docs/README.md)
- The documented PipeConfig options:
  - `BEFORE`: all registers at the inputs.
  - `AFTER`: all registers at the outputs.
  - `INSIDE`: all registers at roughly the middle (falls back to BEFORE if not possible).
  - `DISTRIBUTED`: "evenly distributed to INSIDE, BEFORE, and AFTER (if no INSIDE, all BEFORE)".
  - Source: [cvfpu docs/README.md](https://github.com/openhwgroup/cvfpu/blob/develop/docs/README.md)

**CVA6 FPU configuration (local)**
- `fpu_wrap.sv`: `PipeConfig: fpnew_pkg::DISTRIBUTED`; UnitTypes ADDMUL = PARALLEL, DIVSQRT = MERGED, NONCOMP = PARALLEL, CONV = MERGED. — [core/fpu_wrap.sv](https://github.com/openhwgroup/cva6/blob/master/core/fpu_wrap.sv) (local, lines 78–96)
- `ariane_pkg.sv` latencies: `LAT_COMP_FP32 = 2`, `LAT_COMP_FP64 = 3`, `LAT_DIVSQRT = 2`, `LAT_NONCOMP = 1`, `LAT_CONV = 2`. — [core/include/ariane_pkg.sv](https://github.com/openhwgroup/cva6/blob/master/core/include/ariane_pkg.sv) (local, lines 46–53)

**Register distribution under DISTRIBUTED (local)**
- In `fpnew_cast_multi.sv` and `fpnew_fma.sv` (DISTRIBUTED): `NUM_MID_REGS = (N+2)/3` ("first"), `NUM_INP_REGS = (N+1)/3` ("second"), `NUM_OUT_REGS = N/3` ("last"). For N = 1/2/3/4/5 that gives in/mid/out = 0/1/0, 1/1/0, 1/1/1, 1/2/1, 2/2/1. — [cvfpu src/fpnew_cast_multi.sv](https://github.com/openhwgroup/cvfpu/blob/develop/src/fpnew_cast_multi.sv), [src/fpnew_fma.sv](https://github.com/openhwgroup/cvfpu/blob/develop/src/fpnew_fma.sv) (local, lines 87–101 and 77–90 respectively)
- `fpnew_noncomp.sv` (DISTRIBUTED): `NUM_INP_REGS = (N+1)/2`, `NUM_OUT_REGS = N/2`. With `LAT_NONCOMP = 1` that is 1 input register and 0 output registers. — [cvfpu src/fpnew_noncomp.sv](https://github.com/openhwgroup/cvfpu/blob/develop/src/fpnew_noncomp.sv) (local)

**Path from the FPU to CVA6 (local)**
- `fpnew_top.sv` and `fpnew_opgroup_block.sv` contain no flip-flops; their output arbitration is `rr_arb_tree`.
- `fpu_wrap` sets `fpu_out_ready = 1'b1` and drives `result_o`/`tag_o` straight out.
- In `ex_stage.sv`: `assign fpu_result_o = fpu_valid ? fpu_result : alu_result[1];`
- Sources: [cvfpu src/fpnew_top.sv](https://github.com/openhwgroup/cvfpu/blob/develop/src/fpnew_top.sv), [core/ex_stage.sv](https://github.com/openhwgroup/cva6/blob/master/core/ex_stage.sv) (local)

**Upstream changes and FPGA results**
- cvfpu release history (search extract, not opened in full): v0.6.0 "moved pipelines into the datapath modules"; v0.7.0 fixed the shift-amount width in fma and fma_multi. Neither note is tied to FPGA timing. — [cvfpu releases](https://github.com/openhwgroup/cvfpu/releases)
- The only documented FPGA fix is OOC synthesis of `fpnew_fma` (or a wrapper around the FPU) with retiming, imported as a DCP. It was reported as working by a second user, with no numbers given. — [openhwgroup/cva6#2895](https://github.com/openhwgroup/cva6/issues/2895)

### Inferences
- **Cheapest fix for the conversion path (RTL-configuration change):**
  - Set `LAT_CONV` from 2 to 3. With DISTRIBUTED that gives in/mid/out = 1/1/1, so the cast result is registered before the combinational FPU arbiters and CVA6 writeback. This removes the cast datapath from the path that currently fails.
  - Set `LAT_COMP_FP32` from 2 to 3 for the same reason on FP32 FMA results. Consider `LAT_NONCOMP` from 1 to 2.
  - Alternative: switch PipeConfig to `AFTER`. That is global (one PipeConfig for all units) and would remove input/middle registers elsewhere, so it is riskier.
  - Cost: one more cycle of latency on FP conversions/FP32 ops.
  - Why CVA6 should accept it: fpnew uses tags and CVA6 passes `trans_id` as the tag, so CVA6 already handles variable FPU latency. This must still be confirmed in simulation/regression, because I did not find documentation that other latency values are tested upstream.
- **For the FMA internal path:**
  - Raising `LAT_COMP_FP64` from 3 to 4 gives 1/2/1. That adds a second middle register, but it still relies on retiming to move it to the right place.
  - The alternative with no latency change is to make retiming actually happen on the existing registers (Q5): OOC synthesis of the FPU at a tighter period, or RETIMING attributes.
- **Retiming cannot remove the 0-output-register structure of the cast unit unless it moves the middle register forward.** Synthesis retiming only does that if it sees the path failing, and it does not retime across a module boundary that is kept as hierarchy. So adding the register (LAT_CONV = 3) is more deterministic than hoping for retiming.

### Gaps
- No published FPGA Fmax comparison of cvfpu PipeConfig/PipeRegs settings, either standalone or inside CVA6.
- I did not confirm whether CVA6's verification regressions exercise non-default `LAT_*` values.

## Q3. PMP: known timing issues and optimizations (CVA6 and similar cores)

### Takeaway
I found no upstream CVA6 change, issue or paper that targets PMP timing on FPGA. CVA6's `pmp_entry` recomputes the NAPOT mask combinationally every cycle from the quasi-static `pmpaddr` CSR: a PLEN-wide leading-zero count, a variable shift, an AND and a compare, per entry, for 8 entries. That explains the 31-level path. `PMPNapotEn = 0` only makes NAPOT writes to `pmpcfg` ineffective (they are ignored); it does not remove the decode logic, and it would break software that uses NAPOT. The standard remedy is to precompute and register the mask/base when the CSR is written, which is an RTL change. Other cores (Rocket, Ibex) also check PMP combinationally. Ibex used a timing-motivated configuration knob in its PMP configuration, but it was ASIC-oriented.

### Cited Findings
**CVA6 RTL (local)**
- `pmp_entry.sv`:
  - NAPOT path: `conf_addr_n = {2'b11, ~conf_addr_i}` → `lzc #(.WIDTH(PLEN), .MODE(1'b0))` → `size = trail_ones + 3`, `mask = '1 << size`, `base = (conf_addr_i << 2) & mask`, `match_o = (addr_i & mask) == base`.
  - TOR uses two magnitude comparators.
  - No registers are inside the module.
  - Last functional changes: "Make PMP disableable (#2692)" (Jan 2025) and a formatting fix (#2705).
  - Sources: [core/pmp/src/pmp_entry.sv](https://github.com/openhwgroup/cva6/blob/master/core/pmp/src/pmp_entry.sv) (local), [PR #2692](https://github.com/openhwgroup/cva6/pull/2692) (title from local git log)
- `csr_regfile.sv` line 2711: `if ((!CVA6Cfg.PMPNapotEn && pmpcfg_d[i].addr_mode == riscv::NAPOT) || pmpcfg_d[i].addr_mode == riscv::NA4) pmpcfg_next[i].addr_mode = pmpcfg_q[i].addr_mode;`. So `PMPNapotEn` only legalizes WARL writes; NA4 is never supported. — [core/csr_regfile.sv](https://github.com/openhwgroup/cva6/blob/master/core/csr_regfile.sv) (local)
- `cv64a6_imafdc_sv39_config_pkg.sv`: `CVA6ConfigNrPMPEntries = 8`, `PMPNapotEn: bit'(1)`, `PMPEntryReadOnly: 64'd0`. — [core/include/cv64a6_imafdc_sv39_config_pkg.sv](https://github.com/openhwgroup/cva6/blob/master/core/include/cv64a6_imafdc_sv39_config_pkg.sv) (local)

**CVA6 release notes and issues**
- Release notes: CV32A60X 6.0.0 has "No PMP entries"; v5.2.0 has "PMP independent from MMU". Neither mentions timing. — [CVA6 releases](https://github.com/openhwgroup/cva6/releases)
- The only public report of PMP as a long path is the ASIC one: pmp paths >1 ns at 28 nm / 0.8 ns **[ASIC]**. — [openhwgroup/cva6#3104](https://github.com/openhwgroup/cva6/issues/3104)

**Other cores**
- Rocket: the PMPChecker "is a combinatorial logic circuit that takes in the address and the size of a memory access". This comes from a search extract; the paper is about verification, not timing. — [Cheang et al., SECRISC-V 2020](https://people.eecs.berkeley.edu/%7Ekrste/papers/cheang-secriscv2020.pdf)
- Ibex **[ASIC]** (from search extracts of the Ibex README vendored in OpenTitan):
  - The "maxperf-pmp-bmfull" configuration (16 PMP regions) sets a SpecBranch parameter that "helps timing but has a small negative performance impact".
  - Area is 58.74 kGE (Yosys) vs 35.64 kGE for "maxperf". CoreMark/MHz is 3.05 vs 3.13.
  - Source: [Ibex README (OpenTitan vendor copy)](https://opensecura.googlesource.com/3p/lowrisc/opentitan/+show/270c637e957461815172b87d080e8ec778e89de0/hw/vendor/lowrisc_ibex/README.md)

### Inferences
- **The NAPOT decode depends only on `pmpaddr_q`**, which changes only on CSR writes. So `{mask, base}` per entry can be computed and registered on the cycle after a `pmpaddr`/`pmpcfg` write. This takes the 56-bit LZC and barrel shift off the LSU path, leaving AND + equality-compare + priority. This is an RTL change in `csr_regfile`/`pmp`. The one-cycle update delay must be checked against the privileged-spec ordering rules for PMP writes. I have not verified those rules here.
- **Reducing `NrPMPEntries`** (configuration only) cuts the priority/OR fan-in and area, but not the per-entry depth. It also needs a check of how many entries OpenSBI uses on our platform (not researched). `NrPMPEntries = 0` exists upstream (CV32A60X) but removes PMP isolation of M-mode firmware.
- **`PMPNapotEn = 0` is not a timing fix.** The NAPOT logic stays (synthesis does not prove that a sequential state is unreachable). OpenSBI normally programs NAPOT regions, so NAPOT writes would be silently ignored. This is inferred from common OpenSBI behaviour, not verified here.
- **A `set_multicycle_path` from `pmpaddr_q`/`pmpcfg_q` would fix only the STA report.** It is functionally unsafe unless the RTL guarantees that new PMP values are not consumed for N cycles, and the current RTL makes no such guarantee.

### Gaps
- No public FPGA measurement of CVA6 PMP path depth or its sensitivity to `NrPMPEntries`.
- No upstream or mailing-list discussion of precomputing NAPOT masks found for CVA6, Rocket/BOOM or CV32E40S. The CV32E40S PMP was not researched in depth.
- The number of PMP entries OpenSBI needs on CVA6 was not researched.

## Q4. `FpgaEn` and other FPGA-friendly options in CVA6: what they change and the reported effect

### Takeaway
`FpgaEn = 1` replaces flip-flop arrays with RAM primitives. The integer and FP register files become async-read LUTRAM (`ariane_regfile_fpga`). The BTB moves to BRAM, the BHT to a 3-port async-read memory, and the instruction queue, AXI-adapter, write-buffer and AMO FIFOs use RAM via `cva6_fifo_v3`. The I-cache and D-cache already use `sram_cache` wrappers regardless of `FpgaEn`. These were Thales area optimizations (2022–2023). The PRs report **no frequency or resource numbers**, so its effect on our critical paths is unknown and has to be measured.

### Cited Findings
**What `FpgaEn` switches (local)**
- `issue_read_operands.sv`: `if (CVA6Cfg.FpgaEn) begin : gen_fpga_regfile` instantiates `ariane_regfile_fpga`. There is also a `gen_fpga_fp_regfile` branch for the FP register file. — [core/issue_read_operands.sv](https://github.com/openhwgroup/cva6/blob/master/core/issue_read_operands.sv) (local, lines 910, 972)
- `btb.sv` uses `gen_fpga_btb` (BRAM). `bht.sv` uses `gen_asic_bht` only when `!FpgaEn`. `frontend.sv` uses `vpc_btb = FpgaEn ? icache_dreq_i.vaddr : icache_vaddr_q`, so the BRAM is addressed one cycle early to absorb its registered read. — [core/frontend/btb.sv](https://github.com/openhwgroup/cva6/blob/master/core/frontend/btb.sv), [core/frontend/frontend.sv](https://github.com/openhwgroup/cva6/blob/master/core/frontend/frontend.sv) (local)
- `cva6_fifo_v3.sv` (`gen_fpga_queue`) is used when `FPGA_EN` is set. `FPGA_EN(CVA6Cfg.FpgaEn)` is passed by:
  - `instr_queue`
  - `wt_axi_adapter` (6 FIFOs)
  - `wt_dcache_wbuffer`
  - `amo_buffer`
  - `acc_dispatcher`
  - `std_cache_subsystem`
  - `cva6.sv`
  - Sources: [core/cva6_fifo_v3.sv](https://github.com/openhwgroup/cva6/blob/master/core/cva6_fifo_v3.sv) (local, grep)
- The caches instantiate `sram_cache` (I-cache: `cva6_icache.sv` lines 460/485; D-cache: `wt_dcache_mem.sv` lines 308/335) whatever the `FpgaEn` value. `sram_cache.sv` is described as "SRAM wrapper for FPGA" with an `OUT_REGS` option ("read lat = 2"). — [core/cache_subsystem/cva6_icache.sv](https://github.com/openhwgroup/cva6/blob/master/core/cache_subsystem/cva6_icache.sv), [common/local/util/sram_cache.sv](https://github.com/openhwgroup/cva6/blob/master/common/local/util/sram_cache.sv) (local)

**PR history**
- PR #1016 "add btb optimized for FPGA targets" (merged 2022-12-15): "predictable adresses are stored in BRAM for FPGA and in D flip-flops for ASIC". Flushing is not supported on FPGA. zarubaf asked about the performance impact and got no numbers. — [openhwgroup/cva6#1016](https://github.com/openhwgroup/cva6/pull/1016)
- PR #1038 "Optimize regfile implementation for fpga target" (merged 2023-01-30): the description is just "Regfile optimized for FPGA target", with no metrics. — [openhwgroup/cva6#1038](https://github.com/openhwgroup/cva6/pull/1038)
- Related commits in local git history:
  - #1000 "Config cache fpga" (2022-11-25)
  - #1032 "Add Fifo v3 to optimize fpga implementation in resource size" (2023-01-23)
  - #1039 "BHT optimized for fpga" (2023-02-01): saturation counters in "a three-port asynchronous read memory for the FPGA version"; "FPGA flushing is not supported".
  - #2521 "Fixed btb for FPGA targets" (2024-10-02)
  - #2586 "Dev/hpdcache fpga" (2024-11-07)
  - Sources: [#1032](https://github.com/openhwgroup/cva6/pull/1032), [#1039](https://github.com/openhwgroup/cva6/pull/1039) (titles/messages from local `git log`)
- PR #2592 "Altera opt 1" (2024-11-15) explains that "the optimization previously done for Xilinx" uses "asynchronous RAM primitives". Altera needs synchronous RAM, so `FpgaAlteraEn` adds a synchronous-RAM FIFO variant. — [openhwgroup/cva6#2592](https://github.com/openhwgroup/cva6/pull/2592) (commit message, local git log)
- `cv64a6_imafdc_sv39_config_pkg.sv` has `FpgaEn: bit'(0)`. Release v5.1.0 says "Use cv32a6_imac_sv32 to generate FPGA bitstream". — [CVA6 releases](https://github.com/openhwgroup/cva6/releases), local config pkg

### Inferences
- **`FpgaEn = 1` is a pure configuration change** that mainly removes flip-flops and large read-mux trees: 2 × 32 × 64-bit register files with several read ports, plus the BTB, BHT and FIFOs. Less congestion could help the routing-dominated paths (operands→LSU, issue_read_operands).
- **It also moves the register-file read onto an async LUTRAM read.** That read is not obviously faster than a flop + mux tree, so the net timing effect is unknown and needs one build to measure. A cheap A/B experiment is worthwhile.
- **Functional caveats are documented:** no BTB/BHT flush on FPGA. Predictors are only hints, so this should be performance-only.
- **Async reset:** the 2018 maintainers' estimate (~4 % frequency) suggests async-reset flops have a small cost on FPGA. This is not measured on US+.

### Gaps
- No published LUT/FF/LUTRAM or Fmax numbers for `FpgaEn = 0` vs `1` on any device.
- The upstream FPGA bitstream configuration (`cv32a6_imac_sv32` / `cv32a6_ima_sv32_fpga`) and whether it enables `FpgaEn` were not checked here.

## Q5. Tool-flow techniques (no RTL change) used for CVA6 or similar soft cores in Vivado, and typical gains

### Takeaway
The documented levers are:
- Synthesis global retiming. It is timing-driven and off by default on non-Versal parts, so it moves nothing if the synthesis-time delay estimate says the path passes. That matches our "0 registers moved".
- Forcing retiming via an OOC FPU synthesis at a tight period, or via per-register RETIMING attributes, which are not timing-driven.
- `phys_opt_design` retiming (forward only; cannot cross DSP/BRAM).
- Placement-stage overconstraint with `set_clock_uncertainty -setup` (max 0.5 ns per UG949), removed before routing.
- Checking paths with zero net delay to separate logic problems from placement problems.

I found no CVA6-specific published gains for strategies, pblocks or `phys_opt` retiming. The only CVA6 data point is qualitative: OOC retiming of the FPU "fixed" timing. I found no evidence that an MMCM instead of `pl_clk0` improves STA slack.

### Cited Findings
**Synthesis retiming**
- UG901 (2025.2): `-global_retiming` takes on/off/auto, default `auto`, which turns retiming **on for Versal and off for non-Versal**, so UltraScale+ needs `-global_retiming on` explicitly. It "seeks to improve circuit performance for intra-clock sequential paths by automatically moving registers (register balancing) across combinatorial gates or LUTs". From a search extract; the page itself did not render. — [UG901 Running Synthesis with Tcl](https://docs.amd.com/r/en-US/ug901-vivado-synthesis/Running-Synthesis-with-Tcl)
- UG901 RETIMING_FORWARD/RETIMING_BACKWARD attributes: "Unlike the retiming global setting, this attribute is not timing driven and will work regardless of whether the retiming global setting is active or if there are even timing constraints." Cells with "DONT_TOUCH/MARK_DEBUG attributes, cells with timing exceptions (false_path, multicycle_path), and user instantiated cells will block this attribute." From a search extract. — [UG901 RETIMING_FORWARD (2022.1)](https://docs.amd.com/r/2022.1-English/ug901-vivado-synthesis/RETIMING_FORWARD), [UG901 RETIMING_BACKWARD](https://docs.amd.com/r/en-US/ug901-vivado-synthesis/RETIMING_BACKWARD)
- CVA6 practice: OOC synthesis of `fpnew_fma` or an FPU wrapper with `-retiming -mode out_of_context`, then DCP import. Reported working by 2 users; no numbers. — [openhwgroup/cva6#2895](https://github.com/openhwgroup/cva6/issues/2895)

**Implementation (phys_opt, overconstraint, diagnosis)**
- UG904 physical synthesis:
  - Supports `PSIP_RETIMING_BACKWARD`/`PSIP_RETIMING_FORWARD` properties. "Multi-level retiming is supported by applying the property to all LUT primitives along the path."
  - Retiming does not work for "Moving logic across macro, such as BRAM, UltraRAM, and DSPs", "Paths with different startpoint/endpoint clocks", "Paths with timing exceptions", or cells with "DONT_TOUCH, ASYNC_REG".
  - "Critical-Cell Optimization replicates cells in failing paths."
  - Source: [UG904 Physical Synthesis Phase (2021.2)](https://docs.amd.com/r/2021.2-English/ug904-vivado-implementation/Physical-Synthesis-Phase)
- UG904 (2021.x): the `phys_opt_design` retiming optimization "supports forward retiming" (search extract). In UG835 `-retime` appears in the `phys_opt_design` syntax. — [UG904 Retiming (2021.2)](https://docs.amd.com/r/2021.2-English/ug904-vivado-implementation/Retiming), [UG835 phys_opt_design (2024.1)](https://docs.amd.com/r/2024.1-English/ug835-vivado-tcl-commands/phys_opt_design)
- UG949 "Overconstraining the Design":
  - "Overconstrain only the clocks or clock crossing that cannot meet setup timing."
  - "Use the `-setup` option to tighten the setup requirement only."
  - "Reset the extra uncertainty before running the router step."
  - The value should be at least the violation.
  - "Do not overconstrain beyond 0.5 ns."
  - Source: [UG949 Overconstraining the Design](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Overconstraining-the-Design)
- UG949 incremental flows: overconstraining can hurt incremental reuse. The guide suggests removing it at the placer or using `incr.ignore_user_clock_uncertainty` (search extract). — [UG949 Avoid Floorplanning and Overconstraining](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Avoid-Floorplanning-and-Overconstraining)
- UG949 "Dealing with High Levels of Logic": "To evaluate if a path with high logic-level delay is meeting timing, you can generate timing reports with no net delay." and "Timing closure cannot be achieved on paths that are still violating timing with no net delays." — [UG949 (2023.1)](https://docs.amd.com/r/2023.1-English/ug949-vivado-design-methodology/Dealing-with-High-Levels-of-Logic)
- UG949 "Timing Closure": post-synthesis timing uses estimated net delays, not actual routing delays (search extract). — [UG949 Timing Closure](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Timing-Closure)

**PS-generated PL clocks vs MMCM**
- PYNQ forum on a Zynq US+ board **[US+]**:
  - pynqzen: "The PS PLLs that are used for these PL clocks are good PLLs but are simpler PLLs"; "The distribution to the PL logic is also not as good as other clocking options"; "look into the Clocking Wizard IP for Ultrascale+ which can achieve closer to the desired clock values"; "changing the settings of the PLL can also change the clock's jitter".
  - The original poster got 98.88 MHz instead of 100 MHz.
  - Source: [PYNQ forum: Incorrect PL clocks on PYNQ-ZU](https://discuss.pynq.io/t/incorrect-pl-clocks-on-pynq-zu-board-from-tul/8039)

### Inferences
- **Why our global retiming moved 0 registers while the VC707 flow moved 524:**
  - Global retiming is timing-driven, and our synthesis estimate showed the FPU paths passing. With 60–65 % of delay in routing, the synthesis wire-load estimate is optimistic. On VC707 (slower 7-series fabric), the estimate presumably showed failing FPU paths, so retiming ran.
  - Ways to make it act on the K26:
    - (a) OOC synthesis of `fpnew_top`/`fpu_wrap` at a deliberately tight period (e.g. 6–7 ns) with `-global_retiming on`, imported as a DCP. This is the #2895 recipe.
    - (b) A synthesis-only XDC with a tighter `clk_pl_0` period, or extra `set_clock_uncertainty`, used only in synth_1.
    - (c) `RETIMING_BACKWARD`/`RETIMING_FORWARD` attributes on the specific `mid_pipe`/`out_pipe` registers in fpnew. These are not timing-driven.
  - Things that block it: MARK_DEBUG/DONT_TOUCH on FPU nets (e.g. from ILA debug), `keep_hierarchy`, or timing exceptions touching those registers.
- **Overconstraining has a narrow window.** Our gap is 0.553 ns, and UG949 caps overconstraint at 0.5 ns. Expect it to recover only part of the gap, and only if pre-route timing already looks close.
- **Debug cores:** the project is named `ariane_kr260_debug`, so check for ILA/MARK_DEBUG. ILA probes add fan-out and routing, and MARK_DEBUG blocks retiming and some optimizations. Building once without debug cores is a low-cost experiment. The gain is unknown and design-dependent; no CVA6 source quantifies it.
- **MMCM vs PS clock:**
  - In STA, a PS `PLCLK` constrained only with `create_clock` (no `set_input_jitter`, as in our PS8 XDC; see Q6) carries only system jitter.
  - Putting an MMCM in the path adds the MMCM's discrete jitter to clock uncertainty, so STA slack may get slightly *worse*, not better.
  - An MMCM's real benefits are an exact frequency (e.g. 95 MHz), clean distribution and multiple related clocks.
  - Check the "Clock Uncertainty" breakdown in `report_timing` on a failing path before investing. This is inference from Vivado's uncertainty model, not measured on our design.
- **Pblocks:** UG949 has a section titled "Avoid Floorplanning and Overconstraining". CVA6 on the K26 (ZU5EV-class) leaves a lot of placement freedom, so a pblock is more likely to help by keeping the core near the PS AXI/HP interface than by itself. No CVA6 data exists.

### Gaps
- No public numbers for Performance_* strategies, `phys_opt_design -directive AggressiveExplore`/`-retime`, pblocks or incremental flows on CVA6 or similar 64-bit application cores.
- I could not render the UG901/UG904 pages directly (docs.amd.com returned navigation only). The quotes come from search extracts, so re-check them against the Vivado 2026.1 docs, especially whether Vivado 2026.1 still behaves as "auto = off for non-Versal".
- No measured PS-PLCLK vs MMCM jitter values for the PL on Zynq US+ were found.

## Q6. Common mistakes when porting CVA6 to Zynq UltraScale+ and a check of our methodology

### Takeaway
I found no single public CVA6/Zynq US+ porting post-mortem. There are several known pitfalls:
- The PL clock frequency the PS actually produces can differ from the requested value. It is programmed by the FSBL from the XSA, not by the bitstream, and the PS IP's XDC uses the requested period with no jitter term.
- Changing the CVA6 frequency also requires updating the bootrom UART divisor and the DTS.
- Synthesis estimates are optimistic for routing-dominated paths.
- The -2LV part runs at 0.72 V, so comparisons with -2 Kintex US+ results are not like-for-like.

Our local snapshots show both a correct case (90.909 requested → 90.908180 MHz actual, constraint slightly conservative) and a stale BD (150 requested → 142.855713 MHz actual) in some 100 MHz screening runs. Those runs override the clock in Tcl, so they are not wrong, but the BD has to be fixed before building real 100 MHz hardware.

### Cited Findings
**PS clock constraint and actual frequency**
- Our generated PS8 IP XDC contains only `create_clock -name clk_pl_0 -period "40" [get_pins "PS8_i/PLCLK[0]"]`, with no `set_input_jitter`. It was generated for a 25 MHz request with an actual 24.999750 MHz. — local file `/home/nachofalchi/data/fpga-work/ariane_kr260_debug_ps_generated_backup/ariane_kr260_debug.gen/sources_1/bd/ariane_kr260_ps_bd/ip/ariane_kr260_ps_bd_zynq_ultra_ps_e_0_0/ariane_kr260_ps_bd_zynq_ultra_ps_e_0_0.xdc` (line 21)
- The same pattern (single `create_clock` on `PS8_i/PLCLK[0]` at 10 ns, no jitter) appears in a public Zynq US+ example. — [MicroZed Chronicles PS8 XDC](https://github.com/ATaylorCEngFIET/MicroZed-Chronicles/blob/master/IPI/IPI.srcs/sources_1/bd/design_1/ip/design_1_zynq_ultra_ps_e_0_0/design_1_zynq_ultra_ps_e_0_0.xdc)
- Zynq-7000 contrast **[Zynq-7000]**: an AMD forum thread shows the PS7 IP XDC with `set_input_jitter clk_fpga_0` 0.6 ns (search extract). This is a different PS and does not apply to PS8 as-is. — [AMD Adaptive Support: Zynq clock jitter from PLL](https://adaptivesupport.amd.com/s/question/0D52E00006hpZL6SAM/zynq-clock-jitter-from-pll?language=en_US)
- Requested vs actual PL0 frequency in our BD files (local):
  - Current project BD: `PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ = 90.909`, `ACT_FREQMHZ = 90.908180`, source IOPLL.
  - `backups/pre_91mhz_20261022/kr260_ps_ddr_bd.bd` and the BDs copied into `timing-preparation/synthesis_screen_100MHz/runs/*/source/...`: requested `150`, actual `142.855713`.
  - Files: `/home/nachofalchi/data/fpga-work/cva6-equipo/corev_apu/fpga/ariane_kr260_debug/ariane_kr260_debug.srcs/sources_1/bd/kr260_ps_ddr_bd/kr260_ps_ddr_bd.bd`, `/home/nachofalchi/data/fpga-work/timing-preparation/synthesis_screen_100MHz/runs/no_share/source/corev_apu/fpga/ariane_kr260_debug/ariane_kr260_debug.srcs/sources_1/bd/kr260_ps_ddr_bd/kr260_ps_ddr_bd.bd`
- The screening script overrides the clock: `create_clock -name clk_pl_0 -period [expr {1000.0/$mhz}] ...` (lines 83 and 143), so those runs are analyzed at the intended period regardless of the BD value. — local file `/home/nachofalchi/data/fpga-work/timing-preparation/synthesis_screen_100MHz/code/synthesize.tcl`
- PL clocks come from simpler PS PLLs and are set to "the nearest achievable frequency" (e.g. 98.88 MHz instead of 100 MHz on a PYNQ-ZU **[US+]**). — [PYNQ forum](https://discuss.pynq.io/t/incorrect-pl-clocks-on-pynq-zu-board-from-tul/8039)
- "PS-PL CLKs will be initialised by FSBL which depends on your XSA from your vivado project", so a stale FSBL/XSA gives a different real frequency (search extract, Trenz forum **[US+]**). — [Trenz forum](https://forum.trenz-electronic.de/index.php/topic,1474.0.html)

**Other porting pitfalls**
- CVA6 frequency changes need matching software. In #1749 the user had to change `uart_init(100000000, 115200)` in the bootrom and the DTS clock values (`cv64a6.dts`, `cv64a6_genesysII.dts`), regenerate `bootrom_64.sv` and rebuild Linux. Otherwise the serial output was garbled. — [openhwgroup/cva6#1749](https://github.com/openhwgroup/cva6/issues/1749)
- The upstream Genesys2 XDC handles JTAG/reset as asynchronous: `set_max_delay` 20 ns on `tdo/tms/tdi/trst_n`, `set_false_path -from trst_n`, and a false path from the MIG reset synchronizer. In #77 the user added a false path on `*cdc_to*/D` to keep reset paths out of the report. — [genesys-2.xdc](https://github.com/openhwgroup/cva6/blob/master/corev_apu/fpga/constraints/genesys-2.xdc) (local, lines 120–127), [pulp-platform/ariane#77](https://github.com/pulp-platform/ariane/issues/77)
- In #77 the maintainer advised registering I/O and noted the core has no interrupt synchronizers, so they must be added outside the core. — [pulp-platform/ariane#77](https://github.com/pulp-platform/ariane/issues/77)
- Post-synthesis timing uses estimated net delays, and the "maximal frequency" seen after synthesis can differ from post-implementation, especially at high utilization. — [UG949 Timing Closure](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Timing-Closure), [01signal: Vivado maximal frequency after synthesis](https://www.01signal.com/vendor-specific/xilinx/vivado-minimal-period/)
- -2LV = -2L at VCCINT 0.72 V, with reduced performance compared with 0.85 V operation. — [DS923 Speed Grade Designations](https://docs.amd.com/r/en-US/ds923-virtex-ultrascale-plus/Speed-Grade-Designations), [K26 SOM datasheet](https://www.sundance.com/wp-content/uploads/docs/k26-som-Data-Sheet.pdf)

### Inferences (methodology check)
1. **The closed 90.9 MHz build looks consistent.** The hardware runs at 90.908180 MHz, slightly *below* 90.909, so a 11.000 ns constraint is a slightly pessimistic analysis. That is safe.
2. **For any 100 MHz build that goes to hardware:**
   - Set the BD's PL0 to 100 MHz (not 150 as in the older snapshots) and check that `ACT_FREQMHZ ≤ 100` (IOPLL division rarely gives exactly 100.000).
   - Make sure the XDC `create_clock` override matches it. Look for Vivado's "clock overrides" warning when a user `create_clock` replaces the PS IP's clock.
   - Re-export the XSA and rebuild the FSBL/boot image, because the FSBL programs the real frequency.
   - Update the bootrom UART divisor and the DTS `clock-frequency`/`timebase-frequency`.
3. **Timing analyzed at a different period than the hardware** is the main risk class here. With the screening-script override, an STA "pass" at 10 ns says nothing about a bitstream whose BD/FSBL produces 142.86 MHz. The opposite case (hardware faster than the constraint) can also happen if the IP-generated constraint is overridden with a looser period.
4. **Clock-domain checks:** confirm with `report_clock_interaction`/`report_cdc` that every crossing between `clk_pl_0` and other clocks (PS AXI HP0 if clocked differently, JTAG/debug `tck`, any MMCM outputs) is either synchronous by construction or covered by `set_clock_groups -asynchronous`/`set_max_delay -datapath_only`. Also confirm with `check_timing` that there are no unconstrained endpoints. An unconstrained crossing can make WNS look better than reality.
5. **Retiming setting:** confirm that synthesis saw the intended clock (`report_clocks` on the synthesized DCP). If the PS BD was out-of-context, the in-context clock comes from the BD frequency. The 0-moved-registers result is expected for timing-driven retiming when the estimate passes (Q5); it is not by itself a sign of misconfiguration.
6. **Expectations:** after an extensive physical-optimization campaign the remaining 0.553 ns (5.5 %) is in the range where tool-only measures (overconstraint ≤ 0.5 ns, forced FPU retiming, removing debug cores) might close 100 MHz. Removing the structural causes (`LAT_CONV`/`LAT_COMP_FP32` +1, PMP mask precompute) is more deterministic. This is a judgment call from the cited constraints; no source quantifies it for CVA6.

### Gaps
- I found no official AMD statement on the jitter of PS8 `PLCLK` outputs or on whether Vivado models it. The PS8 XDC has no jitter term, and DS925 only specifies the PS_REF_CLK input jitter (3 ps RMS, 50 ps p-p over 10,000 cycles, from a search extract; [DS925 PS Clocks](https://docs.amd.com/r/en-US/ds925-zynq-ultrascale-plus/PS-Clocks)).
- The exact `ACT_FREQMHZ` the IOPLL produces for a 100 MHz request on our board was not checked. It depends on the IOPLL VCO setting in the BD.
- I did not audit the team's top-level XDC/CDC constraints line by line. Only the files listed above were inspected.
