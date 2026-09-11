# Create and synthesize the KR260-specific ILA and VIO IP with Vivado IP
# Catalog.  Source this script only after a project has been created.
#
# The generated XCI files live under fpga/ip/kr260_debug and are independent
# from the legacy VC707 xlnx_ila IP.

set_param general.maxThreads 1

set debug_ip_root [file normalize [file join [file dirname [info script]] .. ip kr260_debug]]
file mkdir $debug_ip_root

proc kr260_get_or_create_ip {module_name core_name ip_root} {
    set xci [file join $ip_root $module_name $module_name.xci]
    set existing [get_ips -quiet $module_name]
    if {[llength $existing] == 1} {
        return $existing
    }
    if {[file exists $xci]} {
        read_ip $xci
    } else {
        create_ip -name $core_name -vendor xilinx.com -library ip \
            -module_name $module_name -dir $ip_root
    }
    set created [get_ips -quiet $module_name]
    if {[llength $created] != 1} {
        error "Could not create or load $module_name"
    }
    return $created
}

set ila_ip [kr260_get_or_create_ip kr260_axi_ila ila $debug_ip_root]
set_property -dict [list \
    CONFIG.C_NUM_OF_PROBES {21} \
    CONFIG.C_PROBE0_WIDTH {64} \
    CONFIG.C_PROBE1_WIDTH {13} \
    CONFIG.C_PROBE2_WIDTH {64} \
    CONFIG.C_PROBE3_WIDTH {5} \
    CONFIG.C_PROBE4_WIDTH {64} \
    CONFIG.C_PROBE5_WIDTH {13} \
    CONFIG.C_PROBE6_WIDTH {64} \
    CONFIG.C_PROBE7_WIDTH {11} \
    CONFIG.C_PROBE8_WIDTH {4} \
    CONFIG.C_PROBE9_WIDTH {1} \
    CONFIG.C_PROBE10_WIDTH {32} \
    CONFIG.C_PROBE11_WIDTH {1} \
    CONFIG.C_PROBE12_WIDTH {64} \
    CONFIG.C_PROBE13_WIDTH {1} \
    CONFIG.C_PROBE14_WIDTH {1} \
    CONFIG.C_PROBE15_WIDTH {64} \
    CONFIG.C_PROBE16_WIDTH {64} \
    CONFIG.C_PROBE17_WIDTH {8} \
    CONFIG.C_PROBE18_WIDTH {8} \
    CONFIG.C_PROBE19_WIDTH {4} \
    CONFIG.C_PROBE20_WIDTH {20} \
    CONFIG.C_DATA_DEPTH {2048} \
    CONFIG.C_INPUT_PIPE_STAGES {0} \
] $ila_ip

set vio_ip [kr260_get_or_create_ip kr260_reset_vio vio $debug_ip_root]
set_property -dict [list \
    CONFIG.C_NUM_PROBE_IN {1} \
    CONFIG.C_PROBE_IN0_WIDTH {2} \
    CONFIG.C_NUM_PROBE_OUT {1} \
    CONFIG.C_PROBE_OUT0_WIDTH {1} \
    CONFIG.C_PROBE_OUT0_INIT_VAL {0x1} \
] $vio_ip

foreach ip [list $ila_ip $vio_ip] {
    set xci [get_files -of_objects [get_filesets sources_1] [get_property IP_FILE $ip]]
    if {[llength $xci] != 1} {
        set xci [get_files -quiet */[get_property NAME $ip].xci]
    }
    if {[llength $xci] != 1} {
        error "Expected exactly one XCI for [get_property NAME $ip], got: $xci"
    }
    generate_target {instantiation_template} $xci
    generate_target all $xci
    create_ip_run $xci

    set run_name "[get_property NAME $ip]_synth_1"
    set ip_run [get_runs -quiet $run_name]
    if {[llength $ip_run] != 1} {
        set ip_dcp [file join [file dirname $xci] "[get_property NAME $ip].dcp"]
        if {![file exists $ip_dcp]} {
            error "Neither IP synthesis run $run_name nor checkpoint $ip_dcp exists"
        }
        puts "KR260_DEBUG_IP_STATUS:$run_name=Reused complete checkpoint $ip_dcp"
        continue
    }

    # Reconfiguration can invalidate the old OOC result. Reset only this IP
    # run when stale; do not rerun an unchanged, complete VIO unnecessarily.
    if {[get_property NEEDS_REFRESH $ip_run]} {
        reset_run $ip_run
    } else {
        set status [get_property STATUS $ip_run]
        if {[string match "*Complete*" $status] && ![string match "*Failed*" $status]} {
            puts "KR260_DEBUG_IP_STATUS:$run_name=Reused up-to-date run"
            continue
        }
    }
    launch_runs $ip_run -jobs 1
    wait_on_run $ip_run

    set status [get_property STATUS $ip_run]
    puts "KR260_DEBUG_IP_STATUS:$run_name=$status"
    if {![string match "*Complete*" $status] || [string match "*Failed*" $status]} {
        error "IP synthesis failed for $run_name: $status"
    }
}
