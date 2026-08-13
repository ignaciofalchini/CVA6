CROSS_COMPILE ?= riscv64-unknown-elf-
RISCV_TOOLCHAIN_BIN ?=

ifneq ($(strip $(RISCV_TOOLCHAIN_BIN)),)
TOOL_PREFIX := $(RISCV_TOOLCHAIN_BIN)/$(CROSS_COMPILE)
else
TOOL_PREFIX := $(CROSS_COMPILE)
endif

CC := $(TOOL_PREFIX)gcc
OBJCOPY := $(TOOL_PREFIX)objcopy
OBJDUMP := $(TOOL_PREFIX)objdump
READELF := $(TOOL_PREFIX)readelf
GEN_ROM ?= ../gen_rom.py

TARGET := bootrom_kr260_memory_test
CFLAGS := -march=rv64im_zicsr -mabi=lp64 -mcmodel=medany -mexplicit-relocs
LDFLAGS := -nostdlib -nodefaultlibs -nostartfiles -static \
	-Wl,--build-id=none -Wl,--no-gc-sections -T linker.lds

.PHONY: all verify clean

all: $(TARGET).elf $(TARGET).bin $(TARGET).img $(TARGET).sv $(TARGET).h \
	$(TARGET).dis

$(TARGET).elf: memory_test.S linker.lds
	$(CC) $(CFLAGS) $(LDFLAGS) memory_test.S -o $@

$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@

$(TARGET).img: $(TARGET).bin
	dd if=$< of=$@ bs=128 status=none

$(TARGET).sv $(TARGET).h &: $(TARGET).img $(GEN_ROM)
	$(GEN_ROM) $(TARGET).img

$(TARGET).dis: $(TARGET).elf
	$(OBJDUMP) -d -M no-aliases,numeric $< > $@

verify: all
	$(READELF) -h $(TARGET).elf
	$(READELF) -A $(TARGET).elf

clean:
	$(RM) $(TARGET).elf $(TARGET).bin $(TARGET).img $(TARGET).sv \
		$(TARGET).h $(TARGET).dis
