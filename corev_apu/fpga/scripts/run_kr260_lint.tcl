# KR260 RTL compile/elaboration check for environments without a dedicated
# SystemVerilog linter.  This script never launches implementation or writes a
# bitstream.

if {![info exists ::env(XILINX_PART)] || ![info exists ::env(XILINX_BOARD)]} {
    error "XILINX_PART and XILINX_BOARD must be set"
}
if {![info exists ::env(KR260_LINT_REPORT_DIR)]} {
    error "KR260_LINT_REPORT_DIR must be set"
}

set project ariane_kr260_lint
set project_dir [file normalize $project]
set report_dir [file normalize $::env(KR260_LINT_REPORT_DIR)]
file mkdir $report_dir

set_param general.maxThreads 1
create_project $project $project_dir -force -part $::env(XILINX_PART)
set_property board_part $::env(XILINX_BOARD) [current_project]

set include_dirs [list \
    "../../vendor/pulp-platform/common_cells/include" \
    "../../vendor/pulp-platform/axi/include" \
    "../../core/cache_subsystem/hpdcache/rtl/include" \
    "../register_interface/include" \
    "../../core/include" \
]
set_property include_dirs $include_dirs [current_fileset]

source scripts/add_sources.tcl
if {[info exists ::env(KR260_MEMORY_TEST_BOOTROM)] &&
    $::env(KR260_MEMORY_TEST_BOOTROM) eq "1"} {
    source scripts/select_kr260_memory_test_bootrom.tcl
}
set_property top ariane_kr260 [current_fileset]
update_compile_order -fileset sources_1

# Export Vivado's resolved synthesis order for an independent xvlog pass.
set project_file [open [file join $report_dir kr260_xvlog.f] w]
foreach source [get_files -compile_order sources -used_in synthesis] {
    set file_type [get_property FILE_TYPE $source]
    if {$file_type eq "Verilog" || $file_type eq "SystemVerilog" ||
        $file_type eq "Verilog Header"} {
        puts $project_file "\"[file normalize $source]\""
    }
}
close $project_file

# synth_design -rtl performs Vivado RTL elaboration without logic synthesis,
# implementation, placement, routing, or bitstream generation.
synth_design -rtl -name kr260_lint_rtl
report_compile_order -used_in synthesis -file [file join $report_dir compile_order.rpt]

set blackboxes [get_cells -hier -filter {IS_BLACKBOX == 1}]
set unexpected_blackboxes [list]
set blackbox_file [open [file join $report_dir rtl_blackboxes.rpt] w]
puts $blackbox_file "RTL black-box instances before synthesis optimization: [llength $blackboxes]"
foreach blackbox $blackboxes {
    set reference [get_property REF_NAME $blackbox]
    puts $blackbox_file "$blackbox ($reference)"
    # common_cells/unread is an intentional one-input/no-output warning sink.
    # Full synthesis removes these instances, as confirmed by the minimal
    # KR260 synthesis run.  Any other black box remains an error.
    if {![string match "unread*" $reference]} {
        lappend unexpected_blackboxes $blackbox
    }
}
puts $blackbox_file "Unexpected RTL black-box instances: [llength $unexpected_blackboxes]"
close $blackbox_file
if {[llength $unexpected_blackboxes] != 0} {
    error "Unexpected RTL black boxes found"
}

puts "KR260_RTL_ELABORATION=SUCCESS"
close_project
