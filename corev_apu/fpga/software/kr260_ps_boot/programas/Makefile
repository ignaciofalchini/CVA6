# Programas RISC-V para cargar en la DDR por JTAG.
RISCV_TOOLCHAIN_BIN ?= /home/nachofalchi/data/fpga-work/Xilinx/2026.1/gnu/riscv/lin/bin
PREFIX := $(RISCV_TOOLCHAIN_BIN)/riscv64-unknown-elf-
OUT ?= .
FLAGS := -static -nostdlib -nostartfiles -march=rv64im_zicsr -mabi=lp64 -mcmodel=medany -mexplicit-relocs

all: $(OUT)/memory_test_ddr.bin

$(OUT)/%.elf: %.S programa.ld
	$(PREFIX)gcc $(FLAGS) -T programa.ld $< -o $@

$(OUT)/%.bin: $(OUT)/%.elf
	$(PREFIX)objcopy -O binary $< $@
	$(PREFIX)objdump -d $< > $(OUT)/$*.dis

clean:
	rm -f $(OUT)/*.elf $(OUT)/*.bin $(OUT)/*.dis

.PHONY: all clean
.PRECIOUS: $(OUT)/%.elf
