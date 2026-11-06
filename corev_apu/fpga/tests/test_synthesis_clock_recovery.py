from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1]/'scripts/timing_matrix_project.tcl'

HARNESS = r'''
set actual [lindex $argv 0]
set root [lindex $argv 1]
set argv [list synth $root/design.xpr $root $root/recipes current 100 $root/output.dcp]
set argc [llength $argv]
set clock_present 0
set period 7
set completed 0
set hook {}
proc set_param {args} {}
proc open_project {args} {}
proc close_project {} {}
proc get_files {args} {return {}}
proc get_filesets {args} {return sources_1}
proc get_runs {args} {return [lindex $args end]}
proc create_run {args} {}
proc add_files {args} {}
proc set_property {prop value obj} {if {$prop eq "STEPS.SYNTH_DESIGN.TCL.POST"} {set ::hook $value}}
proc get_property {prop obj} {
 if {$prop eq "STATUS"} {return [expr {$::completed ? "synth_design Complete!" : "Not started"}]}
 if {$prop eq "NEEDS_REFRESH"} {return 0}
 if {$prop eq "PERIOD"} {return $::period}
 if {$prop eq "SOURCE_PINS"} {return PS8_i/PLCLK}
 if {$prop eq "STEPS.SYNTH_DESIGN.TCL.POST"} {return $::hook}
 if {[string match *IS_ENABLED $prop]} {return [expr {![string match *POWER* $prop]}]}
 if {[string match *DIRECTIVE $prop]} {return Explore}
 if {$prop eq "FLOW"} {return flow}
 return {}
}
proc list_property_value {args} {return {{Vivado Synthesis Defaults} Flow_PerfThresholdCarry}}
proc update_compile_order {args} {}
proc reset_run {args} {}
proc launch_runs {args} {}
proc get_pins {args} {return pin}
proc get_cells {args} {return {}}
proc get_clocks {args} {if {$::clock_present} {return clk_pl_0}; return {}}
proc create_clock {args} {
 set ::clock_present 1
 set ::period [lindex $args [expr {[lsearch -exact $args -period]+1}]]
}
proc read_xdc {path} {
 set f [open $path]; set text [read $f]; close $f
 foreach line [split $text \n] {
  if {[string trim $line] ne "" && ![regexp {^create_clock\s} $line]} {error "Unsupported non-XDC command"}
 }
 uplevel #0 $text
}
proc wait_on_run {args} {
 # Vivado removes synthesis-only constraints before running the post-hook.
 set ::clock_present 0
 uplevel #0 [list source $::hook]
 set ::completed 1
}
proc open_run {args} {set ::clock_present 1; set ::period 7}
proc write_checkpoint {args} {close [open [lindex $args end] w]}
foreach command {report_clocks report_utilization report_timing_summary check_timing report_timing} {
 proc $command {args} {
  set path [lindex $args [expr {[lsearch -exact $args -file]+1}]]
  set f [open $path w]; puts $f $::period; close $f
 }
}
source $actual
if {$period != 10} {error "Linked clock was not reapplied at 100 MHz"}
'''


class SynthesisClockTest(unittest.TestCase):
    def test_reloads_synthesis_only_clock_before_post_check(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            harness=root/'harness.tcl'
            harness.write_text(HARNESS)
            result=subprocess.run(['tclsh', str(harness), str(SCRIPT), str(root)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(float((root/'synthesis_clock.rpt').read_text()), 10)
            self.assertTrue((root/'output.dcp').exists())


if __name__ == '__main__':
    unittest.main()
