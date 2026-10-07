// SPDX-License-Identifier: Apache-2.0
// DDR bring-up: two complementary address-dependent passes over 16 KiB,
// followed by sparse probes across the full 1 GiB window. Cache disabled by
// KR260_MEMORY_TEST_BOOTROM. Observe terminal PCs and DDR status via ILA/PS.
// PS physical status = 0x800004000 (CVA6 0x80004000):
//   +0: 0 running, 1 pass, -1 fail; +8 address; +16 expected; +24 observed.
.section .text.init
.option norvc
.align 3
.globl _start, test_pass, test_fail
_start:
  li s0, 0x80000000
  li s1, 0x80004000
  sd zero, 0(s1)
  sd zero, 8(s1)
  sd zero, 16(s1)
  sd zero, 24(s1)
  li s2, 0x55aa55aa55aa55aa
  li s3, 2
write_pass:
  mv t0, s0
write_loop:
  xor t1, t0, s2
  sd t1, 0(t0)
  addi t0, t0, 8
  bne t0, s1, write_loop
  fence iorw, iorw
  mv t0, s0
read_loop:
  xor t1, t0, s2
  ld t2, 0(t0)
  bne t1, t2, test_fail
  addi t0, t0, 8
  bne t0, s1, read_loop
  not s2, s2
  addi s3, s3, -1
  bnez s3, write_pass
  // Write ALL sparse probes before reading any, detecting address aliases.
  mv t0, s0
  jal ra, write_probe
  li s4, 0x2000
sparse_write:
  add t0, s0, s4
  jal ra, write_probe
  slli s4, s4, 1
  li t3, 0x40000000
  bltu s4, t3, sparse_write
  li t0, 0xbffffff8
  jal ra, write_probe
  fence iorw, iorw
  mv t0, s0
  jal ra, read_probe
  li s4, 0x2000
sparse_read:
  add t0, s0, s4
  jal ra, read_probe
  slli s4, s4, 1
  li t3, 0x40000000
  bltu s4, t3, sparse_read
  li t0, 0xbffffff8
  jal ra, read_probe
  fence iorw, iorw
  li t1, 1
  sd t1, 0(s1)
  fence iorw, iorw
test_pass:
  j test_pass
write_probe:
  xor t1, t0, s2
  sd t1, 0(t0)
  ret
read_probe:
  xor t1, t0, s2
  ld t2, 0(t0)
  bne t1, t2, test_fail
  ret
test_fail:
  sd t0, 8(s1)
  sd t1, 16(s1)
  sd t2, 24(s1)
  fence iorw, iorw
  li t3, -1
  sd t3, 0(s1)
  fence iorw, iorw
fail_halt:
  j fail_halt
