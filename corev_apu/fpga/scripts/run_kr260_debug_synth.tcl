# KR260 debug-wrapper elaboration and synthesis-only flow.
# No implementation, placement, routing, or bitstream commands are present.

if {![info exists ::env(XILINX_PART)] || ![info exists ::env(XILINX_BOARD)]} {
    error "XILINX_PART and XILINX_BOARD must be set"
}
if {![info exists ::env(KR260_DEBUG_REPORT_DIR)]} {
    error "KR260_DEBUG_REPORT_DIR must be set"
}

set project ariane_kr260_debug
set project_dir [file normalize $project]
set report_dir [file normalize $::env(KR260_DEBUG_REPORT_DIR)]
file mkdir $report_dir

set_param general.maxThreads 1
create_project $project $project_dir -force -part $::env(XILINX_PART)
set_property board_part $::env(XILINX_BOARD) [current_project]

set_property include_dirs [list \
    "../../vendor/pulp-platform/common_cells/include" \
    "../../vendor/pulp-platform/axi/include" \
    "../../core/cache_subsystem/hpdcache/rtl/include" \
    "../register_interface/include" \
    "../../core/include" \
] [current_fileset]

source scripts/add_sources.tcl
set debug_wrapper [file normalize src/ariane_kr260_debug.sv]
if {[llength [get_files -quiet $debug_wrapper]] == 0} {
    add_files -fileset sources_1 -norecurse $debug_wrapper
}

# ariane_kr260 is a top in the minimal project but a child in this project.
# Declare the macro-only headers explicitly so its AXI/RVFI typedef macros do
# not depend on incidental source ordering when the hierarchy changes.
set global_macro_headers [list \
    [file normalize ../../core/include/rvfi_types.svh] \
    [file normalize ../../vendor/pulp-platform/axi/include/axi/assign.svh] \
    [file normalize ../../vendor/pulp-platform/axi/include/axi/typedef.svh] \
]
foreach header $global_macro_headers {
    if {[llength [get_files -quiet $header]] == 0} {
        add_files -fileset sources_1 -norecurse $header
    }
}
set_property file_type {Verilog Header} [get_files $global_macro_headers]
set_property is_global_include 1 [get_files $global_macro_headers]

source scripts/create_kr260_debug_ips.tcl

set_property top ariane_kr260_debug [current_fileset]
update_compile_order -fileset sources_1
add_files -fileset constrs_1 -norecurse constraints/kr260.xdc

synth_design -rtl -name kr260_debug_rtl
report_compile_order -used_in synthesis \
    -file [file join $report_dir debug_compile_order.rpt]

launch_runs synth_1 -jobs 1
wait_on_run synth_1

set synth_status [get_property STATUS [get_runs synth_1]]
puts "KR260_DEBUG_SYNTH_STATUS=$synth_status"
if {![string match "*Complete*" $synth_status] || [string match "*Failed*" $synth_status]} {
    error "KR260 debug synthesis did not complete successfully: $synth_status"
}

open_run synth_1
report_utilization -hierarchical \
    -file [file join $report_dir ariane_kr260_debug.utilization.rpt]
report_timing_summary \
    -file [file join $report_dir ariane_kr260_debug.timing_summary.rpt]
check_timing -verbose \
    -file [file join $report_dir ariane_kr260_debug.check_timing.rpt]

set blackboxes [get_cells -hier -filter {IS_BLACKBOX == 1}]
set expected_blackboxes {}
set unexpected_blackboxes {}
foreach blackbox $blackboxes {
    set ref_name [get_property REF_NAME $blackbox]
    if {$ref_name eq "unread" || $ref_name eq "dbg_hub" || $blackbox eq "dbg_hub"} {
        lappend expected_blackboxes $blackbox
    } else {
        lappend unexpected_blackboxes $blackbox
    }
}
set blackbox_file [open [file join $report_dir ariane_kr260_debug.blackboxes.rpt] w]
puts $blackbox_file "Expected black-box instances: [llength $expected_blackboxes]"
foreach blackbox $expected_blackboxes {
    puts $blackbox_file "$blackbox (REF_NAME=[get_property REF_NAME $blackbox])"
}
puts $blackbox_file "Unexpected black-box instances: [llength $unexpected_blackboxes]"
foreach blackbox $unexpected_blackboxes {
    puts $blackbox_file $blackbox
}
close $blackbox_file
if {[llength $unexpected_blackboxes] != 0} {
    error "Unexpected black boxes found in synthesized debug design"
}

set ila_cells [get_cells -quiet i_kr260_axi_ila]
set debug_file [open [file join $report_dir debug_core_instances.rpt] w]
puts $debug_file "ILA hierarchy cells: [llength $ila_cells]"
foreach cell $ila_cells {
    puts $debug_file $cell
}
puts $debug_file "VIO hierarchy cells: [llength $vio_cells]"
foreach cell $vio_cells {
    puts $debug_file $cell
}
if {[llength $ila_cells] == 1} {
    set ila_core [get_debug_cores -quiet i_kr260_axi_ila]
    puts $debug_file "ILA debug cores: [llength $ila_core]"
    foreach port [lsort [get_debug_ports -of_objects $ila_core]] {
        puts $debug_file "$port width=[get_property PORT_WIDTH $port]"
    }
}
if {[llength $vio_cells] == 1} {
    set vio_core [get_debug_cores -quiet i_kr260_reset_vio]
    puts $debug_file "VIO debug cores: [llength $vio_core]"
    foreach port [lsort [get_debug_ports -of_objects $vio_core]] {
        puts $debug_file "$port width=[get_property PORT_WIDTH $port]"
    }
}
close $debug_file
if {[llength $ila_cells] == 0 || [llength $vio_cells] == 0} {
    error "ILA or VIO hierarchy was not retained in synthesis"
}

write_checkpoint -force [file join $report_dir ariane_kr260_debug_synth.dcp]
file copy -force [get_property DIRECTORY [get_runs synth_1]]/runme.log \
    [file join $report_dir synth_1.runme.log]
puts "KR260 debug synthesis complete; no implementation or bitstream was run"
