// SPDX-License-Identifier: Apache-2.0
// Prueba de memoria para ejecutar desde DDR. El codigo queda en 0x80000000.
// Zona de prueba desde 0x80100000; buzon en 0xBFFFF000 (PS 0x83FFFF000):
//   +0: 0 en curso, 1 PASS, -1 fallo de memoria, -2 excepcion
//   +8, +16, +24: direccion, esperado, leido (o mepc, mcause, mtval).
.section .text.init
.option norvc
.align 3
.globl _start
_start:
  la t0, trap
  csrw mtvec, t0
  li s0, 0x80100000          // inicio de la zona de prueba
  li s5, 0x80104000          // fin de la zona densa (16 KiB)
  li s1, 0xBFFFF000          // buzon
  sd zero, 0(s1)
  sd zero, 8(s1)
  sd zero, 16(s1)
  sd zero, 24(s1)
  fence iorw, iorw
  li s2, 0x55aa55aa55aa55aa
  li s3, 2
write_pass:
  mv t0, s0
write_loop:
  xor t1, t0, s2
  sd t1, 0(t0)
  addi t0, t0, 8
  bne t0, s5, write_loop
  fence iorw, iorw
  mv t0, s0
read_loop:
  xor t1, t0, s2
  ld t2, 0(t0)
  bne t1, t2, test_fail
  addi t0, t0, 8
  bne t0, s5, read_loop
  not s2, s2
  addi s3, s3, -1
  bnez s3, write_pass
  // Primero se escriben todas las sondas, para detectar direcciones repetidas.
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
.align 2
trap:
  li s1, 0xBFFFF000
  csrr t0, mepc
  csrr t1, mcause
  csrr t2, mtval
  sd t0, 8(s1)
  sd t1, 16(s1)
  sd t2, 24(s1)
  fence iorw, iorw
  li t3, -2
  sd t3, 0(s1)
  fence iorw, iorw
trap_halt:
  j trap_halt
