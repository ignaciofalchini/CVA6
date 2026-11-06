# Analyze a saved, linked synthesized checkpoint without modifying it.
if {$argc != 2} {error "Expected: linked_synthesis.dcp report_directory"}
lassign $argv checkpoint outdir
file mkdir $outdir
set_param general.maxThreads 1
open_checkpoint $checkpoint
if {![llength [get_clocks -quiet]]} {error "No clocks in the supplied checkpoint"}
set f [open [file join $outdir report_context.txt] w]
puts $f "Vivado: [version -short]"
puts $f "Source checkpoint: $checkpoint"
puts $f "Reconstructed post-synthesis analysis; interconnect delays are estimates."
foreach clk [get_clocks] {puts $f "Clock: $clk; period: [get_property PERIOD $clk] ns"}
close $f
report_clocks -file [file join $outdir clocks.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 20 -input_pins -file [file join $outdir timing_summary.rpt]
report_timing -delay_type max -max_paths 20 -input_pins -file [file join $outdir critical_setup.rpt]
report_timing -delay_type min -max_paths 20 -input_pins -file [file join $outdir critical_hold.rpt]
check_timing -verbose -file [file join $outdir check_timing.rpt]
report_utilization -hierarchical -file [file join $outdir utilization.rpt]
close_design
