// SPDX-License-Identifier: Apache-2.0
// Minimal RV64 DRAM smoke test for observation at the KR260 AXI boundary.

  .section .text.init
  .option norvc
  .align  3
  .globl  _start
  .type   _start, @function

_start:
  // Keep the test independent of interrupt handlers and runtime startup.
  csrw    mie, zero

  li      t0, 0x0000000080000000
  li      t1, 0xa55aa55adeadbeef

  // This address is a cold cache line after reset. The configured write-through
  // D-cache sends the store to AXI; the following load then fills the line from
  // external memory. The test does not disable or reconfigure either cache.
  sd      t1, 0(t0)
  fence   rw, rw
  ld      t2, 0(t0)
  bne     t1, t2, .Lerror

.Lsuccess:
  // Repeated success marker: address +8, pattern 0x600d... .  The loop keeps
  // the result observable in an ILA capture without UART or GPIO.
  li      t3, 0x600d600d600d600d
  sd      t3, 8(t0)
  fence   w, w
  j       .Lsuccess

.Lerror:
  // Repeated error marker: address +16, pattern 0xbad0... .
  li      t3, 0xbad0bad0bad0bad0
  sd      t3, 16(t0)
  fence   w, w
  j       .Lerror

  .size   _start, .-_start
