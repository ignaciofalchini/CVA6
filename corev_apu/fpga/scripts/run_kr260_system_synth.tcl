# Reproducible synthesis-only check of CVA6 -> HP0 -> KR260 PS DDR.

if {![info exists ::env(XILINX_PART)] || ![info exists ::env(XILINX_BOARD)]} {
    error "XILINX_PART and XILINX_BOARD must be set"
}
if {![info exists ::env(KR260_SYSTEM_REPORT_DIR)]} {
    error "KR260_SYSTEM_REPORT_DIR must be set"
}

set_param general.maxThreads 1
set project ariane_kr260_system
set project_dir [file normalize $project]
set report_dir [file normalize $::env(KR260_SYSTEM_REPORT_DIR)]
file mkdir $report_dir

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
if {[info exists ::env(KR260_MEMORY_TEST_BOOTROM)] &&
    $::env(KR260_MEMORY_TEST_BOOTROM) eq "1"} {
    source scripts/select_kr260_memory_test_bootrom.tcl
}

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

source scripts/create_kr260_ps_ddr_bd.tcl
set bd_file [get_files ariane_kr260_ps_bd.bd]
generate_target all $bd_file
make_wrapper -files $bd_file -top -import

set system_top [file normalize src/ariane_kr260_system.sv]
add_files -fileset sources_1 -norecurse $system_top
set_property top ariane_kr260_system [current_fileset]
update_compile_order -fileset sources_1

set bd_report [open [file join $report_dir ps_ddr_bd_configuration.rpt] w]
set ps [get_bd_cells zynq_ultra_ps_e_0]
set hp0 [get_bd_intf_pins $ps/S_AXI_HP0_FPD]
puts $bd_report "Vivado=[version -short]"
puts $bd_report "part=[get_property PART [current_project]]"
puts $bd_report "board=[get_property BOARD_PART [current_project]]"
puts $bd_report "PS=[get_property VLNV $ps]"
foreach property {CONFIG.ADDR_WIDTH CONFIG.DATA_WIDTH CONFIG.ID_WIDTH
                  CONFIG.AWUSER_WIDTH CONFIG.ARUSER_WIDTH CONFIG.FREQ_HZ
                  CONFIG.HAS_BURST CONFIG.HAS_LOCK CONFIG.MAX_BURST_LENGTH
                  CONFIG.NUM_READ_OUTSTANDING CONFIG.NUM_WRITE_OUTSTANDING
                  CONFIG.SUPPORTS_NARROW_BURST} {
    puts $bd_report "HP0.$property=[get_property $property $hp0]"
}
set cva6_space [get_bd_addr_spaces S_AXI_CVA6]
foreach segment [get_bd_addr_segs -of_objects $cva6_space] {
    puts $bd_report "segment=$segment offset=[get_property OFFSET $segment] \
range=[get_property RANGE $segment]"
}
puts $bd_report "PL0.requested_MHz=[get_property \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ $ps]"
puts $bd_report "PL0.actual_MHz=[get_property \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__ACT_FREQMHZ $ps]"
close $bd_report

validate_bd_design
save_bd_design
report_compile_order -used_in synthesis \
    -file [file join $report_dir compile_order.rpt]

launch_runs synth_1 -jobs 1
wait_on_run synth_1
set synth_status [get_property STATUS [get_runs synth_1]]
puts "KR260_SYSTEM_SYNTH_STATUS=$synth_status"
if {![string match "*Complete*" $synth_status] ||
    [string match "*Failed*" $synth_status]} {
    file copy -force [get_property DIRECTORY [get_runs synth_1]]/runme.log \
        [file join $report_dir synth_1.runme.log]
    error "KR260 PS/DDR system synthesis failed: $synth_status"
}

open_run synth_1
report_utilization -hierarchical \
    -file [file join $report_dir ariane_kr260_system.utilization.rpt]
report_timing_summary \
    -file [file join $report_dir ariane_kr260_system.timing_summary.rpt]
check_timing -verbose \
    -file [file join $report_dir ariane_kr260_system.check_timing.rpt]

set blackbox_file [open [file join $report_dir \
    ariane_kr260_system.blackboxes.rpt] w]
set unexpected_blackboxes {}
foreach cell [get_cells -hier -filter {IS_BLACKBOX == 1}] {
    set reference [get_property REF_NAME $cell]
    set expected [expr {$reference eq "unread" ||
                        [string match "zynq_ultra_ps_e*" $reference]}]
    puts $blackbox_file "$cell REF_NAME=$reference expected=$expected"
    if {!$expected} {
        lappend unexpected_blackboxes $cell
    }
}
puts $blackbox_file "Unexpected black boxes: [llength $unexpected_blackboxes]"
close $blackbox_file
if {[llength $unexpected_blackboxes] != 0} {
    error "Unexpected black boxes found in KR260 system synthesis"
}

write_checkpoint -force \
    [file join $report_dir ariane_kr260_system_synth.dcp]
file copy -force [get_property DIRECTORY [get_runs synth_1]]/runme.log \
    [file join $report_dir synth_1.runme.log]
puts "KR260_SYSTEM_SYNTHESIS=SUCCESS"
puts "No implementation or bitstream was run"
