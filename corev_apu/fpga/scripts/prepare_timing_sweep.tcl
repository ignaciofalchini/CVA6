# Export a complete, linked synthesis netlist from the current project.
# Never reset runs, synthesize, save the project, or generate a bitstream here.
if {$argc != 2} { error "Expected: project.xpr output_checkpoint.dcp" }
lassign $argv project output
set_param general.maxThreads 4
puts "TIMING_RESOURCE_MAX_THREADS=4"
open_project $project
set run [get_runs synth_1]
if {[get_property NEEDS_REFRESH $run]} { error "Synthesis is stale; regenerate it before starting a new sweep" }
if {![string match "*Complete*" [get_property STATUS $run]]} { error "Synthesis is not complete" }
foreach {run_name expected} {synth_1 Flow_PerfOptimized_high impl_1 Performance_ExploreWithRemap} {
    if {[get_property STRATEGY [get_runs $run_name]] ne $expected} {
        error "Project strategy changed for $run_name; review sweep directives before proceeding"
    }
}
open_run synth_1
set boxes [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}]
set unexpected {}
foreach box $boxes {
    # Vivado inserts/implements its debug hub during implementation.
    puts "SWEEP_BLACKBOX=$box REF_NAME=[get_property REF_NAME $box]"
    if {$box ne "dbg_hub"} { lappend unexpected $box }
}
if {[llength $unexpected]} { error "Unresolved black boxes in linked synthesis: $unexpected" }
puts "SWEEP_EXPECTED_DEBUG_BLACKBOXES=$boxes"
if {[llength [get_clocks -quiet clk_pl_0]] != 1} { error "Expected primary clk_pl_0 is missing" }
report_clocks -file [file join [file dirname $output] baseline_clocks.rpt]
write_checkpoint -force $output
close_project
