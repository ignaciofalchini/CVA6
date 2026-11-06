# Usage: vivado -mode batch -source timing_sweep.tcl -tclargs synth.dcp clock MHz outdir
if {$argc ni {4 5}} { error "Expected: synthesized_checkpoint clock_name MHz output_directory ?recipe.tcl?" }
lassign $argv checkpoint clock_name mhz outdir recipe
set sweep_opt {opt_design -directive ExploreWithRemap}
set sweep_place {place_design -directive Explore}
set sweep_physopt {phys_opt_design -directive Explore}
set sweep_route {route_design -directive NoTimingRelaxation -tns_cleanup}
set sweep_postroute {phys_opt_design -directive Explore}
if {$recipe ne ""} { source $recipe }
if {![string is double -strict $mhz] || $mhz <= 0} { error "Invalid MHz" }
file mkdir $outdir
set_param general.maxThreads 4
puts "TIMING_RESOURCE_MAX_THREADS=4"
proc save_stage {outdir stage} {
    set target [file join $outdir ${stage}.dcp]
    write_checkpoint -force ${target}.partial.dcp
    file rename -force ${target}.partial.dcp $target
    set fh [open ${target}.ok.partial w]
    puts $fh "timing-sweep-v2 $stage"
    close $fh
    file rename -force ${target}.ok.partial ${target}.ok
    puts "SWEEP_SAVED=$stage"
}
# Only committed checkpoints are eligible. A failed open falls back one stage.
set stages {constrained optimized placed physopt routed final}
set completed -1
for {set i [expr {[llength $stages]-1}]} {$i >= 0} {incr i -1} {
    set stage [lindex $stages $i]
    set candidate [file join $outdir ${stage}.dcp]
    if {![file exists $candidate] || ![file exists ${candidate}.ok]} { continue }
    if {[catch {open_checkpoint $candidate} message]} {
        puts "SWEEP_REJECTED=$stage: $message"
        catch {close_design}
        continue
    }
    set completed $i
    puts "SWEEP_RESUMED=$stage"
    break
}
if {$completed < 0} { open_checkpoint $checkpoint }
set clk [get_clocks -quiet $clock_name]
if {[llength $clk] != 1} { error "Clock must match exactly one clock; available: [get_clocks]" }
if {[get_property IS_GENERATED $clk]} { error "Select a primary clock, not a generated clock" }
set period [expr {1000.0 / $mhz}]
if {$completed >= 0 && abs([get_property PERIOD $clk] - $period) > 0.00001} {
    error "Recovered checkpoint clock period differs from requested period"
}
if {$completed < 0} {
set sources [get_property SOURCE_PINS $clk]
set objects [get_ports -quiet $sources]
if {[llength $objects] == 0} { set objects [get_pins -quiet $sources] }
if {[llength $objects] == 0} { error "Cannot resolve clock source: $sources" }
create_clock -name $clock_name -period $period -waveform [list 0 [expr {$period/2.0}]] $objects
save_stage $outdir constrained
}
foreach report {clocks route_status timing_summary check_timing utilization drc} {
    set old [file join $outdir ${report}.rpt]
    if {[file exists $old]} {
        set archive [file join $outdir report_history [clock microseconds]]
        file mkdir $archive
        file rename $old [file join $archive ${report}.rpt]
    }
}
report_clocks -file $outdir/clocks.rpt
if {$completed < 1} {
    {*}$sweep_opt
    save_stage $outdir optimized
}
if {$completed < 2} {
    {*}$sweep_place
    save_stage $outdir placed
}
if {$completed < 3} {
    if {[llength $sweep_physopt]} { {*}$sweep_physopt }
    save_stage $outdir physopt
}
if {$completed < 4} {
    {*}$sweep_route
    save_stage $outdir routed
}
if {$completed < 5} {
    if {[llength $sweep_postroute]} { {*}$sweep_postroute }
    set unresolved [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}]
    if {[llength $unresolved]} { error "Black boxes remain after implementation: $unresolved" }
    save_stage $outdir final
}
report_route_status -file $outdir/route_status.rpt
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 50 -input_pins -file $outdir/timing_summary.rpt
check_timing -verbose -file $outdir/check_timing.rpt
report_utilization -file $outdir/utilization.rpt
report_drc -file $outdir/drc.rpt
foreach {name command} {
    critical_setup {report_timing -delay_type max -max_paths 100 -nworst 5 -input_pins}
    critical_hold {report_timing -delay_type min -max_paths 50 -input_pins}
    hierarchical_utilization {report_utilization -hierarchical}
    clock_interaction {report_clock_interaction}
    high_fanout {report_high_fanout_nets -max_nets 100 -timing}
    design_analysis {report_design_analysis -timing -congestion}
    methodology {report_methodology}
    bus_skew {report_bus_skew}
    power {report_power}
} {
    if {[catch {{*}$command -file [file join $outdir ${name}.rpt]} message]} {
        set f [open [file join $outdir ${name}.error.txt] w]; puts $f $message; close $f
    }
}
close_design
