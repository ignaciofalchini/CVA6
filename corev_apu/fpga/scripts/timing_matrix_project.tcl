# Run only on a frozen, private copy of the KR260 project.
# mode project.xpr source_root recipes_dir synth_profile MHz ?output.dcp?
if {$argc ni {6 7}} { error "Expected: preflight|synth project source_root recipes profile MHz ?output.dcp?" }
lassign $argv mode project source_root recipes profile mhz output
set_param general.maxThreads 4
puts "TIMING_RESOURCE_MAX_THREADS=4"
open_project $project
set root [file normalize $source_root]
foreach f [get_files -all] {
    set path [file normalize $f]
    if {[string first "${root}/" $path] != 0} { error "External source escaped snapshot: $path" }
    if {![file exists $path]} { error "Missing frozen project source: $path" }
}
foreach dir [get_property INCLUDE_DIRS [get_filesets sources_1]] {
    set dir [file normalize $dir]
    if {[string first "${root}/" $dir] != 0 || ![file isdirectory $dir]} { error "Invalid frozen include directory: $dir" }
}
file mkdir $recipes
proc export_recipe {run path} {
    foreach step {POWER_OPT_DESIGN POST_PLACE_POWER_OPT_DESIGN} {
        if {[get_property STEPS.${step}.IS_ENABLED $run]} { error "Unsupported enabled power optimization step in recipe: $step" }
    }
    set f [open ${path}.partial w]
    foreach {step variable command} {
        OPT_DESIGN sweep_opt opt_design
        PLACE_DESIGN sweep_place place_design
        PHYS_OPT_DESIGN sweep_physopt phys_opt_design
        ROUTE_DESIGN sweep_route route_design
        POST_ROUTE_PHYS_OPT_DESIGN sweep_postroute phys_opt_design
    } {
        set args [list $command]
        set enabled 1
        if {$step in {PHYS_OPT_DESIGN POST_ROUTE_PHYS_OPT_DESIGN}} {
            set enabled [get_property STEPS.${step}.IS_ENABLED $run]
        }
        if {!$enabled} {
            set args {}
        } else {
            set directive [get_property STEPS.${step}.ARGS.DIRECTIVE $run]
            if {$directive ne ""} { lappend args -directive $directive }
            set more [get_property "STEPS.${step}.ARGS.MORE OPTIONS" $run]
            if {$more ne ""} { set args [concat $args $more] }
        }
        puts $f [list set $variable $args]
    }
    close $f
    file rename -force ${path}.partial $path
}
export_recipe [get_runs impl_1] [file join $recipes current.tcl]
foreach {id strategy} {
    explore_postroute Performance_ExplorePostRoutePhysOpt
    extra_timing Performance_ExtraTimingOpt
    netdelay_high Performance_NetDelay_high
    wl_block Performance_WLBlockPlacement
} {
    set name matrix_${id}
    if {![llength [get_runs -quiet $name]]} {
        create_run $name -parent_run synth_1 -flow [get_property FLOW [get_runs impl_1]] -strategy $strategy
    }
    export_recipe [get_runs $name] [file join $recipes ${id}.tcl]
}
foreach strategy {{Vivado Synthesis Defaults} Flow_PerfThresholdCarry} {
    if {$strategy ni [list_property_value STRATEGY [get_runs synth_1]]} { error "Unavailable strategy: $strategy" }
}
if {$mode eq "preflight"} {
    close_project
    exit
}
if {$mode ne "synth"} { error "Unknown mode" }
proc write_if_changed {path text} {
    if {[file exists $path]} {
        set f [open $path r]; set old [read $f]; close $f
        if {$old eq $text} { return }
    }
    set f [open $path w]; puts -nonewline $f $text; close $f
}
# Clock at the PS black-box boundary is available during top-level synthesis.
# It is a synthesis-only nominal constraint; implementation reapplies the period
# to the linked primary clock. The PS physical configuration remains unchanged.
set xdc [file join [file dirname $project] matrix_synthesis_clock.xdc]
set pin {i_ps_ddr/kr260_ps_ddr_bd_i/zynq_ultra_ps_e_0/pl_clk0}
set text [format {create_clock -name clk_pl_0 -period %.9f [get_pins {%s}]} [expr {1000.0/$mhz}] $pin]
append text "\n"
write_if_changed $xdc $text
if {![llength [get_files -quiet $xdc]]} { add_files -fileset constrs_1 -norecurse $xdc }
set_property PROCESSING_ORDER LATE [get_files $xdc]
set_property USED_IN_IMPLEMENTATION false [get_files $xdc]
set run synth_1
if {$profile ne "current"} {
    set strategy [dict get [dict create defaults {Vivado Synthesis Defaults} carry Flow_PerfThresholdCarry alternate Flow_AlternateRoutability] $profile]
    set run matrix_synth
    if {![llength [get_runs -quiet $run]]} {
        create_run $run -srcset sources_1 -constrset constrs_1 -flow [get_property FLOW [get_runs synth_1]] -strategy $strategy
    }
}
set hook [file join [file dirname $project] matrix_verify_synthesis_clock.tcl]
# Project-mode synth writes its checkpoint without synthesis-only constraints.
# Re-read the nominal XDC for this check; do not mistake normal constraint removal
# for a failed synthesis. The run log records the original synthesis application.
set text [list read_xdc $xdc]
append text "\n" {set matrix_clk [get_clocks -quiet clk_pl_0]}
append text "\n" {if {[llength $matrix_clk] != 1} { error "Nominal synthesis clock is missing" }} "\n"
append text [format {if {abs([get_property PERIOD $matrix_clk] - %.9f) > 0.00001} { error "Incorrect synthesis clock period" }} [expr {1000.0/$mhz}]] "\n"
append text [list report_clocks -file [file join [file dirname $project] synthesis_clock.rpt]] "\n"
write_if_changed $hook $text
set previous [get_property STEPS.SYNTH_DESIGN.TCL.POST [get_runs $run]]
if {$previous ne "" && [file normalize $previous] ne [file normalize $hook]} {
    error "Existing synthesis post-hook requires review before combining it with matrix clock verification"
}
set_property STEPS.SYNTH_DESIGN.TCL.POST $hook [get_runs $run]
update_compile_order -fileset sources_1
if {![string match "*Complete*" [get_property STATUS [get_runs $run]]] || [get_property NEEDS_REFRESH [get_runs $run]]} {
    reset_run $run
    launch_runs $run -jobs 1
    wait_on_run $run
}
if {![string match "*Complete*" [get_property STATUS [get_runs $run]]]} { error "Synthesis failed: $run" }
open_run $run
foreach box [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}] {
    if {$box ne "dbg_hub"} { error "Unexpected unresolved IP: $box" }
}
if {[llength [get_clocks -quiet clk_pl_0]] != 1} { error "Linked clock missing" }
set primary [get_clocks clk_pl_0]
set primary_source [get_property SOURCE_PINS $primary]
create_clock -name clk_pl_0 -period [expr {1000.0/$mhz}] -waveform [list 0 [expr {500.0/$mhz}]] [get_pins $primary_source]
write_checkpoint -force $output
report_utilization -file [file join [file dirname $output] synthesis_utilization.rpt]
report_clocks -file [file join [file dirname $output] synthesis_clocks.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 20 -input_pins -file [file join [file dirname $output] synthesis_timing.rpt]
check_timing -verbose -file [file join [file dirname $output] synthesis_check_timing.rpt]
report_timing -delay_type max -max_paths 20 -input_pins -file [file join [file dirname $output] synthesis_critical_setup.rpt]
report_timing -delay_type min -max_paths 20 -input_pins -file [file join [file dirname $output] synthesis_critical_hold.rpt]
close_project
