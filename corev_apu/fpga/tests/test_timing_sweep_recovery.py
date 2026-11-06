"""Fault injection for recovery, without a Vivado license or an FPGA."""
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
RUNNER = SCRIPTS / 'timing_sweep.py'
TCL = SCRIPTS / 'timing_sweep.tcl'

# Exercise the real Tcl state machine with lightweight mocked Vivado commands.
HARNESS = r'''
set actual [lindex $argv 0]
set argv [lrange $argv 1 end]
set argc [llength $argv]
set outdir [lindex $argv 3]
proc trace_step {step} {
 global outdir
 set f [open $outdir/trace.txt a]; puts $f $step; close $f
 if {[info exists ::env(SWEEP_FAIL)] && $step eq $::env(SWEEP_FAIL) && ![file exists $outdir/failed_once]} {
  close [open $outdir/failed_once w]
  error "injected stage interruption"
 }
}
proc set_param {args} {}
proc open_checkpoint {path} {
 set f [open $path]; set data [read $f]; close $f
 if {$data eq "corrupt"} { error "corrupt checkpoint" }
 trace_step "open:[file tail $path]"
}
proc close_design {} {}
proc get_clocks {args} {return clk_pl_0}
proc get_cells {args} {return {}}
proc get_property {prop obj} {
 switch $prop { IS_GENERATED {return 0} PERIOD {return 10.0} SOURCE_PINS {return pin} }
}
proc get_ports {args} {return pin}
proc create_clock {args} {trace_step constrain}
proc write_checkpoint {args} {set f [open [lindex $args end] w]; puts $f checkpoint; close $f}
proc opt_design {args} {trace_step opt}
proc place_design {args} {trace_step place}
proc phys_opt_design {args} {trace_step physopt}
proc route_design {args} {trace_step route}
foreach name {report_clocks report_route_status report_timing_summary check_timing report_utilization report_drc} {
 proc $name {args} {
  set index [lsearch -exact $args -file]
  set f [open [lindex $args [expr {$index+1}]] w]
  puts $f "report"
  close $f
 }
}
source $actual
'''


class RecoveryTest(unittest.TestCase):
    def test_tcl_resumes_committed_stage_and_falls_back_if_corrupt(self):
        import os
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            harness = root / 'harness.tcl'
            harness.write_text(HARNESS)
            checkpoint = root / 'synth.dcp'
            checkpoint.write_text('synthesis')
            out = root / 'run'
            out.mkdir()
            cmd = ['tclsh', str(harness), str(TCL), str(checkpoint), 'clk_pl_0', '100', str(out)]
            env = dict(os.environ, SWEEP_FAIL='route')
            first = subprocess.run(cmd, env=env, capture_output=True, text=True)
            self.assertNotEqual(first.returncode, 0)
            self.assertTrue((out / 'physopt.dcp.ok').exists())
            self.assertFalse((out / 'routed.dcp.ok').exists())
            # A partial checkpoint must never be selected.
            (out / 'routed.dcp.partial.dcp').write_text('partial')
            (out / 'trace.txt').write_text('')
            second = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            trace = (out / 'trace.txt').read_text()
            self.assertTrue(trace.startswith('open:physopt.dcp'))
            self.assertNotIn('place\n', trace)
            self.assertIn('route\n', trace)
            (out / 'final.dcp').write_text('corrupt')
            (out / 'trace.txt').write_text('')
            third = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(third.returncode, 0, third.stderr)
            self.assertIn('SWEEP_REJECTED=final', third.stdout)
            self.assertTrue((out / 'trace.txt').read_text().startswith('open:routed.dcp'))

    def test_runner_interruption_snapshot_and_completed_frequency_skip(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            checkpoint = root / 'synth.dcp'
            checkpoint.write_text('original netlist')
            project = root / 'project.xpr'
            project.write_text('project')
            fake = root / 'vivado'
            fake.write_text('''#!/usr/bin/env python3
import pathlib, sys, time
out = pathlib.Path(sys.argv[-1])
(out/'entered').write_text('yes')
if not (out/'allow').exists():
    time.sleep(30)
for name in ['clocks','route_status','check_timing','utilization','drc']:
    (out/(name+'.rpt')).write_text('report')
(out/'timing_summary.rpt').write_text('WNS(ns) TNS(ns) WHS(ns)\\n------- -------- -------\\n1.0 0 0 10 0.1 0 0 10 0.2 0 0 10\\n')
(out/'final.dcp.ok').write_text('committed')
''')
            fake.chmod(0o755)
            out = root / 'results'
            cmd = [sys.executable, str(RUNNER), '--checkpoint', str(checkpoint), '--project', str(project),
                   '--clock', 'clk_pl_0', '--mhz', '100', '125', '--vivado', str(fake), '--output', str(out)]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 10
                while not (out / '100MHz/entered').exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue((out / '100MHz/entered').exists())
                # A concurrent runner must refuse to use the same directory.
                other = subprocess.run(cmd, capture_output=True, text=True)
                self.assertNotEqual(other.returncode, 0)
                self.assertIn('Another runner', other.stderr)
                process.send_signal(signal.SIGTERM)
                process.communicate(timeout=5)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
            self.assertEqual(json.loads((out / 'state.json').read_text())['status'], 'interrupted')
            checkpoint.write_text('later user synthesis')
            for f in ('100', '125'):
                folder = out / (f+'MHz')
                folder.mkdir(exist_ok=True)
                (folder/'allow').touch()
            resumed = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual((out/'inputs/synth.dcp').read_text(), 'original netlist')
            result = out/'100MHz/result.json'
            before = result.read_bytes()
            again = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertEqual(result.read_bytes(), before)
            self.assertEqual(json.loads(result.read_text())['timing'], 'met')
            frozen_command = cmd.copy()
            frozen_command[1] = str(out/'inputs/timing_sweep.py')
            frozen = subprocess.run(frozen_command, capture_output=True, text=True, timeout=10)
            self.assertEqual(frozen.returncode, 0, frozen.stderr)
            (out/'inputs/synth.dcp').write_text('tampered')
            damaged = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(damaged.returncode, 0)
            self.assertIn('Frozen checkpoint', damaged.stderr)


if __name__ == '__main__':
    unittest.main()
