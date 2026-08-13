OUTPUT_ARCH(riscv)
ENTRY(_start)

SECTIONS
{
    . = 0x0000000000010000;

    .text : ALIGN(8) {
        KEEP(*(.text.init))
        *(.text .text.*)
    }

    .rodata : ALIGN(8) { *(.rodata .rodata.*) }
    .data   : ALIGN(8) { *(.data .data.*) }
    .bss    : ALIGN(8) { *(.bss .bss.* COMMON) }

    _image_end = .;
    ASSERT(_image_end <= 0x0000000000020000,
           "KR260 memory-test bootrom exceeds its 64 KiB window")
}
