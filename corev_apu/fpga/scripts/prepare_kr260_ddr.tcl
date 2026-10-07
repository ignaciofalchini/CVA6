# Update an open KR260 project for DDR integration. No synthesis is launched.
set kr260_fpga_dir [file normalize [file join [file dirname [info script]] ..]]
source [file join $kr260_fpga_dir scripts use_kr260_top.tcl]
set kr260_bd [get_files -quiet */kr260_ps_ddr_bd.bd]
if {[llength $kr260_bd] != 1} { error "Expected one kr260_ps_ddr_bd.bd" }
open_bd_design $kr260_bd
validate_bd_design
generate_target all $kr260_bd
# Explicit Verilog wrapper has flat ports matching kr260_top.
set kr260_wrapper [make_wrapper -files $kr260_bd -top -language Verilog]
foreach f [get_files -quiet */imports/hdl/kr260_ps_ddr_bd_wrapper.v] { remove_files $f }
foreach f $kr260_wrapper {
    if {[llength [get_files -quiet $f]] == 0} { add_files -norecurse $f }
}
foreach f [get_files -quiet */kr260_ps_ddr_bd_sv.sv] { remove_files $f }
foreach f [get_files -quiet */ariane_kr260_ps_bd_wrapper.v] { remove_files $f }
foreach f [get_files -quiet */ariane_kr260_ps_bd.bd] { remove_files $f }
set kr260_pkg [file join $kr260_fpga_dir src kr260_addr_pkg.sv]
if {[llength [get_files -quiet $kr260_pkg]] == 0} { add_files -norecurse $kr260_pkg }
set_property used_in_synthesis true [get_files $kr260_pkg]
set_property used_in_simulation true [get_files $kr260_pkg]
# A cold boot must be gated by PS reset, not require a VIO click.
set kr260_vio [get_ips kr260_reset_vio]
set_property CONFIG.C_PROBE_OUT0_INIT_VAL 0x0 $kr260_vio
generate_target all $kr260_vio
set_property top kr260_top [get_filesets sources_1]
set kr260_defs [get_property verilog_define [get_filesets sources_1]]
if {[lsearch -exact $kr260_defs KR260_MEMORY_TEST_BOOTROM] < 0} {
    lappend kr260_defs KR260_MEMORY_TEST_BOOTROM
    set_property verilog_define $kr260_defs [get_filesets sources_1]
}
set_property AUTO_INCREMENTAL_CHECKPOINT 0 [get_runs synth_1]
set_property INCREMENTAL_CHECKPOINT {} [get_runs synth_1]
update_compile_order -fileset sources_1
puts "KR260_DDR_PREPARED: top=kr260_top; no synthesis launched"
