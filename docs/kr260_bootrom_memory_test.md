# KR260 bootrom memory test

## Purpose and status

This is a deliberately small, separate RV64 bare-metal image for observing the
first accesses to PS DDR at the existing `m_axi_mem_*` boundary. It does not
replace `bootrom_64`: the normal ROM remains the default unless the Vivado
fileset defines `KR260_MEMORY_TEST_BOOTROM`.

The image builds, generates the existing ROM formats, compiles with `xvlog`, and
elaborates as part of `ariane_kr260`. This proves RTL integration only. It has
not run on KR260 hardware and cannot pass until a real PL-to-PS-DDR path exists.

## Test program

Source: `corev_apu/fpga/src/bootrom/kr260_memory_test/memory_test.S`

```asm
_start:
  csrw    mie, zero

  li      t0, 0x0000000080000000
  li      t1, 0xa55aa55adeadbeef
  sd      t1, 0(t0)
  fence   rw, rw
  ld      t2, 0(t0)
  bne     t1, t2, .Lerror

.Lsuccess:
  li      t3, 0x600d600d600d600d
  sd      t3, 8(t0)
  fence   w, w
  j       .Lsuccess

.Lerror:
  li      t3, 0xbad0bad0bad0bad0
  sd      t3, 16(t0)
  fence   w, w
  j       .Lerror
```

The program does not configure UART, GPIO, interrupts, an OS, or a runtime.
The linker places `_start` at `0x0001_0000`, the reset boot-ROM base used by
this FPGA system. The linker also rejects an image larger than the 64 KiB ROM
window ending at `0x0002_0000`.

The configured CVA6 D-cache remains enabled. It is the existing write-through
(`config_pkg::WT`) cache, and `0x8000_0000` is inside its configured cacheable
region. On a cold line after reset, the first store is propagated through the
write buffer to AXI and the subsequent load fills the line from external
memory. No cache, MMU, FPU, or atomic unit is removed or disabled.

## Addresses and recognizable patterns

| Address | Data | Meaning |
| --- | --- | --- |
| `0x0000_0000_8000_0000` | `0xa55a_a55a_dead_beef` | Initial value written and read back |
| `0x0000_0000_8000_0008` | `0x600d_600d_600d_600d` | Repeated success marker |
| `0x0000_0000_8000_0010` | `0xbad0_bad0_bad0_bad0` | Repeated error marker |

Success means only that the value returned by the load equals the initial
pattern. The success loop continuously writes the `0x600d...` marker at `+8`.
Failure branches to a distinct loop that continuously writes `0xbad0...` at
`+16`, making the result visible without an output peripheral.

## What to look for in the ILA

For the initial store, trigger on `AWVALID && AWREADY` with `AWADDR` equal to
`0x8000_0000`. Expect a full 64-bit write (`AWSIZE=3`), `WSTRB=0xff`, W data
`0xa55a_a55a_dead_beef`, and eventually `BVALID && BREADY` with `BRESP=OKAY`.

For the read, look for an AR handshake covering `0x8000_0000`, then an R beat
containing `0xa55a_a55a_dead_beef` with `RRESP=OKAY`. Because this address is a
cold cache line, the cache may request a line-fill burst: use `ARLEN`, `RLAST`,
and the address/beat position rather than assuming a one-beat read.

After the comparison, repeated writes at exactly one of `0x8000_0008` or
`0x8000_0010` identify the success or error loop. The write-through cache makes
these markers observable at `m_axi_mem_*`.

## Generate and verify the ROM

Vivado 2026.1 includes the RV64 bare-metal toolchain used for this check:

```bash
cd corev_apu/fpga/src/bootrom/kr260_memory_test
make verify \
  RISCV_TOOLCHAIN_BIN=/home/nachofalchi/data/fpga-work/Xilinx/2026.1/gnu/riscv/lin/bin
```

The existing `gen_rom.py` flow produces:

- `bootrom_kr260_memory_test.elf`
- `bootrom_kr260_memory_test.bin`
- `bootrom_kr260_memory_test.img`
- `bootrom_kr260_memory_test.sv`
- `bootrom_kr260_memory_test.h`
- `bootrom_kr260_memory_test.dis`

The verified artifact is an ELF64 little-endian RISC-V executable, entry point
`0x10000`, ISA attributes `rv64im_zicsr`, and a 148-byte binary.

## Select it in Vivado

The selector `corev_apu/fpga/scripts/select_kr260_memory_test_bootrom.tcl`
adds the generated module and the compile define without removing the normal
ROM. The lint/elaboration and debug synthesis scripts enable it only when the
environment variable is explicitly set:

```bash
cd corev_apu/fpga
KR260_MEMORY_TEST_BOOTROM=1 \
XILINX_PART=xck26-sfvc784-2LV-c \
XILINX_BOARD=xilinx.com:kr260_som:part0:2.0 \
KR260_LINT_REPORT_DIR="$PWD/../../reports/kr260_next_steps/bootrom" \
vivado -mode batch -source scripts/run_kr260_lint.tcl
```

The executed Vivado RTL elaboration completed with no errors or critical
warnings and retained `bootrom_kr260_memory_test` in the hierarchy. This is not
a DDR simulation and does not demonstrate a hardware memory response. A second
RTL elaboration without the environment variable also completed, confirming
that `bootrom_64` remains the usable default and that the selector is opt-in.
