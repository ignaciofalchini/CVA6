import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0, str(SCRIPTS))
from timing_matrix import closure

CHECKS = ['no_clock', 'unconstrained_internal_endpoints', 'no_input_delay', 'no_output_delay',
          'multiple_clock', 'generated_clocks', 'loops', 'partial_input_delay', 'partial_output_delay', 'latch_loops']


class ProgressiveSearchTest(unittest.TestCase):
    def test_seed_reuse_first_success_advance_and_stop_at_failed_frequency(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root/'repo/corev_apu/fpga/ariane_kr260_debug/ariane_kr260_debug.xpr'
            project.parent.mkdir(parents=True)
            project.write_text('project')
            tool = root/'vivado'
            tool.write_text('''#!/usr/bin/env python3
import pathlib, sys
root = pathlib.Path(__file__).parent
args = sys.argv[sys.argv.index('-tclargs')+1:]
script = pathlib.Path(sys.argv[sys.argv.index('-source')+1]).name
with (root/'trace').open('a') as log: log.write(script+' '+repr(args)+'\\n')
if script == 'timing_matrix_project.tcl':
    folder=pathlib.Path(args[3]); folder.mkdir(parents=True,exist_ok=True)
    for name in ('current','extra_timing','explore_postroute'): (folder/(name+'.tcl')).write_text(name)
    if args[0] == 'synth': pathlib.Path(args[6]).write_text('checkpoint '+args[4]+args[5])
else:
    out=pathlib.Path(args[3])
    passed=float(args[2])==100 and 'extra_timing' in str(out)
    (out/'clocks.rpt').write_text('clocks')
    (out/'route_status.rpt').write_text('# of nets with routing errors..... : 0 :')
    (out/'drc.rpt').write_text('Report DRC\\n| Rule | Severity | Checks |')
    (out/'utilization.rpt').write_text('utilization')
    checks=['no_clock','unconstrained_internal_endpoints','no_input_delay','no_output_delay','multiple_clock','generated_clocks','loops','partial_input_delay','partial_output_delay','latch_loops']
    (out/'check_timing.rpt').write_text('\\n'.join('checking '+c+' (0)' for c in checks))
    slack=1 if passed else -1
    (out/'timing_summary.rpt').write_text('WNS(ns) TNS(ns) WHS(ns)\\n------- -------- -------\\n'+str(slack)+' 0 0 10 0.1 0 0 10 0.2 0 0 10\\n'+('All user specified timing constraints are met.' if passed else 'Timing constraints are not met.'))
    (out/'final.dcp.ok').write_text('committed')
''')
            tool.chmod(0o755)
            base = [sys.executable, str(SCRIPTS/'timing_matrix.py'), '--project', str(project), '--vivado', str(tool)]
            seed = root/'seed'
            cmd = base+['--output', str(seed), '--policy', 'exhaustive', '--mhz', '100', '--synthesis', 'current', '--implementation', 'current']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            out = root/'search'
            cmd = base+['--output', str(out), '--seed-run', str(seed), '--mhz', '100', '125', '150',
                        '--synthesis', 'current', 'defaults', '--implementation', 'current', 'extra_timing']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            progress = json.loads((out/'search_progress.json').read_text())
            self.assertEqual(progress['highest_closed_mhz'], 100)
            self.assertEqual(progress['limiting_mhz'], 125)
            self.assertFalse(progress['range_complete'])
            self.assertEqual(progress['closed'][0]['implementation'], 'extra_timing')
            self.assertFalse((out/'synthesis/defaults/100MHz').exists())
            self.assertFalse((out/'synthesis/current/150MHz').exists())
            self.assertTrue((out/'synthesis/current/100MHz/synthesis.json').exists())
            self.assertTrue((out/'experiments/current/100MHz/current/100MHz/import.json').exists())
            trace = (root/'trace').read_text()
            resumed = cmd.copy(); resumed[1] = str(out/'code/timing_matrix.py')
            result = subprocess.run(resumed, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root/'trace').read_text(), trace)

    def test_positive_slack_does_not_advance_with_unconstrained_paths(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            (out/'result.json').write_text(json.dumps(dict(execution='complete', timing='met')))
            (out/'timing_summary.rpt').write_text('All user specified timing constraints are met.')
            (out/'check_timing.rpt').write_text('\n'.join(f'checking {c} ({3 if c == "no_clock" else 0})' for c in CHECKS))
            (out/'route_status.rpt').write_text('# of nets with routing errors... : 0 :')
            (out/'drc.rpt').write_text('Report DRC')
            verdict, problems=closure(out)
            self.assertEqual(verdict, 'review')
            self.assertIn('no_clock=3', problems)


if __name__ == '__main__':
    unittest.main()
