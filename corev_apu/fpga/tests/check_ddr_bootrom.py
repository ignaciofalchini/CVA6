#!/usr/bin/env python3
"""Execute the actual RV64 test image in a small ISA model, not a CVA6 model.
Checks test control flow, first failure reporting and detection of 8 KiB aliases.
Does not model caches, AXI, DDR timing, or the processor implementation.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / 'src/bootrom/kr260_memory_test'
MASK = (1 << 64) - 1
BASE, END, STATUS = 0x80000000, 0xc0000000, 0x80004000
image = (ROM / 'bootrom_kr260_memory_test.bin').read_bytes()
# Confirm the checked-in hardware ROM encodes the same bytes.
words = re.findall(r"64'h([0-9a-fA-F_]+)", (ROM / 'bootrom_kr260_memory_test.sv').read_text())
hardware = b''.join(int(w.replace('_', ''), 16).to_bytes(8, 'little') for w in reversed(words))
assert hardware[:len(image)] == image


def signed(n, bits):
    return (n & ((1 << (bits - 1)) - 1)) - (n & (1 << (bits - 1)))


def execute(fault=None):
    regs, memory, pc, reads, writes = [0] * 32, {}, 0x10000, set(), set()
    def key(a):
        assert BASE <= a <= END - 8 and a % 8 == 0, hex(a)
        return (a & 0x1fff) if fault == 'alias8k' else a
    for step in range(100000):
        assert 0 <= pc - 0x10000 <= len(image) - 4
        ins = int.from_bytes(image[pc-0x10000:pc-0x10000+4], 'little')
        op, rd, f3 = ins & 127, (ins >> 7) & 31, (ins >> 12) & 7
        rs1, rs2 = (ins >> 15) & 31, (ins >> 20) & 31
        a, b, imm, nxt = regs[rs1], regs[rs2], signed(ins >> 20, 12), pc + 4
        if op == 0x37: regs[rd] = signed(ins & 0xfffff000, 32)
        elif op in (0x13, 0x1b):
            if f3 == 0: val = a + imm
            elif f3 == 1: val = a << ((ins >> 20) & 63)
            elif f3 == 4: val = a ^ imm
            else: raise AssertionError(hex(ins))
            regs[rd] = signed(val & 0xffffffff, 32) if op == 0x1b else val
        elif op == 0x33:
            assert f3 in (0, 4) and ins >> 25 == 0
            regs[rd] = a + b if f3 == 0 else a ^ b
        elif op == 0x23:
            assert f3 == 3
            addr = (a + signed(((ins >> 25) << 5) | ((ins >> 7) & 31), 12)) & MASK
            memory[key(addr)] = b
            writes.add(addr)
        elif op == 0x03:
            assert f3 == 3
            addr = (a + imm) & MASK
            regs[rd] = memory.get(key(addr), 0)
            if fault == 'corrupt' and addr == BASE + 0x80: regs[rd] ^= 1
            reads.add(addr)
        elif op == 0x63:
            offset = signed(((ins >> 31) << 12) | (((ins >> 7) & 1) << 11) |
                            (((ins >> 25) & 63) << 5) | (((ins >> 8) & 15) << 1), 13)
            assert f3 in (1, 6)
            if (a != b if f3 == 1 else a < b): nxt = pc + offset
        elif op == 0x6f:
            offset = signed(((ins >> 31) << 20) | (((ins >> 12) & 255) << 12) |
                            (((ins >> 20) & 1) << 11) | (((ins >> 21) & 1023) << 1), 21)
            regs[rd], nxt = pc + 4, pc + offset
        elif op == 0x67: regs[rd], nxt = pc + 4, (a + imm) & ~1
        elif op == 0x0f: pass
        else: raise AssertionError(f'Unsupported {ins:x} at {pc:x}')
        regs = [r & MASK for r in regs]
        regs[0] = 0
        if nxt == pc:
            return memory, reads, writes, step, key
        pc = nxt
    raise AssertionError('Test did not terminate')

for fault in (None, 'alias8k', 'corrupt'):
    mem, reads, writes, steps, key = execute(fault)
    assert mem[key(STATUS)] == (1 if fault is None else MASK)
    if fault is None:
        assert END - 8 in reads and END - 8 in writes
        assert all(BASE + (1 << n) in reads for n in range(13, 30))
    elif fault == 'corrupt':
        assert mem[key(STATUS+8)] == BASE+0x80
        assert mem[key(STATUS+16)] ^ mem[key(STATUS+24)] == 1
    print(f'PASS {fault or "normal"}: {steps} instructions, {len(reads)} read addresses')
print('PASS generated RTL ROM matches compiled binary')
