/* Programas RISC-V cargados en la DDR. La ROM salta siempre a 0x80000000. */
ENTRY(_start)
SECTIONS
{
    . = 0x80000000;
    .text.init : { KEEP(*(.text.init)) }
    .text      : { *(.text*) }
    .rodata    : { *(.rodata*) *(.srodata*) }
    .data      : { *(.data*) *(.sdata*) }
    .bss (NOLOAD) : { __bss_start = .; *(.sbss*) *(.bss*) *(COMMON); __bss_end = .; }
    /* Sin esto, .note queda en 0x80000000 y el programa no arranca. */
    /DISCARD/ : { *(.note*) *(.comment) *(.riscv.attributes) *(.eh_frame*) }
}
