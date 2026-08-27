// SPDX-License-Identifier: Apache-2.0
// Minimal RV64 sequential DDR write loop for KR260 AXI observation.

  .section .text.init
  .option norvc
  .align  3
  .globl  _start
  .type   _start, @function

_start:
  li      t0, 0x0000000080000000
  li      t1, 0
  li      t2, 1024

.Lwrite:
  sd      t1, 0(t0)
  addi    t0, t0, 8
  addi    t1, t1, 1
  bne     t1, t2, .Lwrite

  li      t0, 0x0000000080000000
  li      t1, 0
  j       .Lwrite

  .size   _start, .-_start
