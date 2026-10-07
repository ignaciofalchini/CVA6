# Batch RTL elaboration only. Never launch synth_1/implementation/bitstream.
set kr260_fpga_dir [file normalize [file join [file dirname [info script]] ..]]
if {![info exists ::env(KR260_DDR_RTL_REPORT_DIR)]} {
    error "KR260_DDR_RTL_REPORT_DIR is not set"
}
set kr260_report_dir [file normalize $::env(KR260_DDR_RTL_REPORT_DIR)]
file mkdir $kr260_report_dir
set_param general.maxThreads 1
open_project [file join $kr260_fpga_dir ariane_kr260_debug ariane_kr260_debug.xpr]
source [file join $kr260_fpga_dir scripts prepare_kr260_ddr.tcl]
report_compile_order -used_in synthesis -file [file join $kr260_report_dir compile_order.rpt]
# -rtl stops after RTL elaboration; it does not perform logic synthesis.
synth_design -rtl -name kr260_ddr_rtl
report_drc -file [file join $kr260_report_dir rtl_drc.rpt]
report_clocks -file [file join $kr260_report_dir rtl_clocks.rpt]
set kr260_boxes [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}]
set kr260_out [open [file join $kr260_report_dir rtl_blackboxes.rpt] w]
foreach c $kr260_boxes { puts $kr260_out "$c [get_property REF_NAME $c]" }
close $kr260_out
if {[llength $kr260_boxes] != 0} { error "Unexpected unresolved RTL black boxes: $kr260_boxes" }
if {[llength [get_cells -quiet i_kr260_axi_ila]] != 1 ||
    [llength [get_cells -quiet i_kr260_reset_vio]] != 1} {
    error "ILA/VIO missing from elaborated hierarchy"
}
if {[llength [get_clocks -quiet clk_pl_0]] != 1} {
    error "PS clock is not constrained"
}
puts "KR260_DDR_RTL_ELABORATION=SUCCESS"
close_project
