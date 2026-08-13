VIVADO ?= vivado
VIVADOFLAGS ?= -nojournal -mode batch -source scripts/prologue.tcl

work-dir := work-fpga
bit := $(work-dir)/ariane_xilinx.bit
mcs := $(work-dir)/ariane_xilinx.mcs
ip-dir := xilinx
ips := xlnx_axi_clock_converter.xci  \
       xlnx_axi_dwidth_converter.xci \
       xlnx_axi_dwidth_converter_dm_master.xci \
       xlnx_axi_dwidth_converter_dm_slave.xci \
       xlnx_axi_quad_spi.xci         \
       xlnx_axi_gpio.xci             \
       xlnx_clk_gen.xci              \
       xlnx_mig_7_ddr3.xci

ips := $(addprefix $(work-dir)/, $(ips))
ips-target := $(join $(addsuffix /ip/, $(addprefix $(ip-dir)/, $(basename $(ips)))), $(ips))

ifeq ($(BOARD),kr260)
KR260_ATTEMPT ?= 1
KR260_REPORT_DIR ?= ../../reports/kr260_port/attempt_$(KR260_ATTEMPT)
KR260_DEBUG_REPORT_DIR ?= ../../reports/kr260_next_steps/debug
export KR260_REPORT_DIR
export KR260_DEBUG_REPORT_DIR

# KR260 is synthesis-only by design.  Do not add implementation or bitstream
# targets here until the physical PS/PL memory and pin architecture is chosen.
all: kr260-synth

kr260-synth:
	mkdir -p $(KR260_REPORT_DIR)
	$(VIVADO) -mode batch -nojournal -log $(KR260_REPORT_DIR)/vivado.log -source scripts/run_kr260_synth_2.tcl

kr260-debug-synth:
	mkdir -p $(KR260_DEBUG_REPORT_DIR)
	$(VIVADO) -mode batch -nojournal -log $(KR260_DEBUG_REPORT_DIR)/vivado.log -source scripts/run_kr260_debug_synth.tcl

.PHONY: kr260-synth kr260-debug-synth

else
all: $(mcs)

# Generate mcs from bitstream
$(mcs): $(bit)
	$(VIVADO) $(VIVADOFLAGS) -source scripts/write_cfgmem.tcl -tclargs $@ $^

$(bit): $(ips)
	mkdir -p $(work-dir)
	$(VIVADO) $(VIVADOFLAGS) -source scripts/run.tcl
	cp ariane.runs/impl_1/ariane_xilinx* ./$(work-dir)

$(ips): %.xci :
	mkdir -p $(work-dir)
	@echo Generating $(@F)
	@cd $(ip-dir)/$(basename $(@F)) && make clean && make
	@cp $(ip-dir)/$(basename $(@F))/$(basename $(@F)).srcs/sources_1/ip/$(basename $(@F))/$(@F) $@

mcs: $(mcs)

endif

program:
	$(VIVADO) $(VIVADOFLAGS) -source scripts/program.tcl

clean:
	rm -rf *.log *.jou *.str *.mif *.xpr $(work-dir) ariane.cache ariane.hw ariane.ip_user_files scripts/vivado*

.PHONY:
	clean
