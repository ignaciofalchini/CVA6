# KR260 synthesis-only project creation and run; no implementation or bitstream.
if {![info exists ::env(XILINX_PART)] || ![info exists ::env(XILINX_BOARD)]} {
    error "XILINX_PART and XILINX_BOARD must be set by the root Makefile"
}
if {![info exists ::env(KR260_REPORT_DIR)]} {
    error "KR260_REPORT_DIR must identify the archived synthesis attempt"
}

set project ariane_kr260
set project_dir [file normalize $project]
set report_dir [file normalize $::env(KR260_REPORT_DIR)]
file mkdir $report_dir

set_param general.maxThreads 1
create_project $project $project_dir -force -part $::env(XILINX_PART)
set_property board_part $::env(XILINX_BOARD) [current_project]

set_property include_dirs { \
    "../../vendor/pulp-platform/common_cells/include" \
    "../../vendor/pulp-platform/axi/include" \
    "../../core/cache_subsystem/hpdcache/rtl/include" \
    "../register_interface/include" \
    "../../core/include" \
} [current_fileset]

# Include paths resolve the shared headers; no board header is read here.

source scripts/add_sources.tcl
set_property top ariane_kr260 [current_fileset]
update_compile_order -fileset sources_1
add_files -fileset constrs_1 -norecurse constraints/kr260.xdc

synth_design -rtl -name rtl_1
launch_runs synth_1 -jobs 1
wait_on_run synth_1

set synth_status [get_property STATUS [get_runs synth_1]]
puts "KR260_SYNTH_STATUS=$synth_status"
if {![string match "*Complete*" $synth_status] || [string match "*Failed*" $synth_status]} {
    error "KR260 synthesis did not complete successfully: $synth_status"
}

open_run synth_1
report_utilization -hierarchical -file $report_dir/ariane_kr260.utilization.rpt
report_timing_summary -file $report_dir/ariane_kr260.timing_summary.rpt
check_timing -verbose -file $report_dir/ariane_kr260.check_timing.rpt

set blackboxes [get_cells -hier -filter {IS_BLACKBOX == 1}]
set blackbox_file [open $report_dir/ariane_kr260.blackboxes.rpt w]
puts $blackbox_file "Unexpected black-box instances: [llength $blackboxes]"
foreach blackbox $blackboxes {
    puts $blackbox_file $blackbox
}
close $blackbox_file
if {[llength $blackboxes] != 0} {
    error "Unexpected black boxes found; see $report_dir/ariane_kr260.blackboxes.rpt"
}

write_checkpoint -force $report_dir/ariane_kr260_synth.dcp
file copy -force [get_property DIRECTORY [get_runs synth_1]]/runme.log $report_dir/synth_1.runme.log
puts "KR260 synthesis complete; reports and DCP are in $report_dir"
