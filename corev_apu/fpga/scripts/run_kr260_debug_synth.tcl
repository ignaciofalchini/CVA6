# KR260 elaboration and synthesis-only flow for the saved GUI project.
# No implementation, placement, routing, or bitstream commands are present.
# Save and close the GUI project before running this script in batch mode.
# The project's BD is the source of truth; backups are never loaded here.

if {![info exists ::env(KR260_DEBUG_REPORT_DIR)]} {
    error "KR260_DEBUG_REPORT_DIR must be set"
}

set project ariane_kr260_debug
set fpga_dir [file normalize [file join [file dirname [info script]] ..]]
set project_dir [file join $fpga_dir $project]
set project_file [file join $project_dir ${project}.xpr]
set bd_source [file join $project_dir ${project}.srcs sources_1 bd \
    ariane_kr260_ps_bd ariane_kr260_ps_bd.bd]
foreach required_file [list $project_file $bd_source] {
    if {![file isfile $required_file]} {
        error "Missing saved GUI project file: $required_file; no backup will be used"
    }
}
if {[llength [current_project -quiet]] != 0} {
    error "Run this script in a fresh Vivado batch session after saving and closing the GUI project"
}
set report_dir [file normalize $::env(KR260_DEBUG_REPORT_DIR)]
file mkdir $report_dir

set_param general.maxThreads 1
open_project $project_file

# Preserve the saved source set, IP settings, constraints and run strategies.
# Never recreate this directory with create_project -force: it contains the
# canonical BD edited by the user in Vivado.
set bd_file [get_files -quiet $bd_source]
if {[llength $bd_file] != 1} {
    error "The saved project must contain the GUI Block Design: $bd_source"
}
puts "KR260_DEBUG_BD_SOURCE=$bd_source"
open_bd_design $bd_file
validate_bd_design
generate_target all $bd_file
set bd_wrapper [make_wrapper -files $bd_file -top -import]
if {[llength $bd_wrapper] == 0 || ![file exists [lindex $bd_wrapper 0]]} {
    error "Could not generate BRAM Block Design wrapper"
}

set_property top ariane_kr260_debug [current_fileset]
update_compile_order -fileset sources_1

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
set vio_cells [get_cells -quiet i_kr260_reset_vio]
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
