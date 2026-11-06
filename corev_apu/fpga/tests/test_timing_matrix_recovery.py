import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


class MatrixRecoveryTest(unittest.TestCase):
    def test_matrix_isolation_resume_and_strategy_separation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root/'repo/corev_apu/fpga/ariane_kr260_debug/ariane_kr260_debug.xpr'
            project.parent.mkdir(parents=True)
            project.write_text('frozen project')
            rtl = project.parent/'design.sv'
            rtl.write_text('original RTL')
            tool = root/'vivado'
            tool.write_text('''#!/usr/bin/env python3
import pathlib, sys
root = pathlib.Path(__file__).parent
args = sys.argv[sys.argv.index('-tclargs')+1:]
script = pathlib.Path(sys.argv[sys.argv.index('-source')+1]).name
trace = root/'trace'
def record(text):
    with trace.open('a') as f: f.write(text+'\\n')
if script == 'timing_matrix_project.tcl':
    mode, project, source, recipes, profile, mhz = args[:6]
    folder = pathlib.Path(recipes); folder.mkdir(parents=True, exist_ok=True)
    for name in ('current','explore_postroute','extra_timing'):
        (folder/(name+'.tcl')).write_text('# '+name)
    if mode == 'synth':
        record('synth '+profile+' '+mhz)
        pathlib.Path(args[6]).write_text('synthesized '+profile+' '+mhz)
else:
    out = pathlib.Path(args[3]); recipe = pathlib.Path(args[4]).stem
    record('route '+args[2]+' '+recipe)
    if args[2] == '125.0' and recipe == 'implementation' and 'extra_timing' in str(out) and not (root/'failed').exists():
        (root/'failed').touch()
        raise SystemExit(1)
    for name in ['clocks','route_status','check_timing','utilization','drc']:
        (out/(name+'.rpt')).write_text('report')
    (out/'timing_summary.rpt').write_text('WNS(ns) TNS(ns) WHS(ns)\\n------- -------- -------\\n-0.1 -1 1 10 0.1 0 0 10 0.2 0 0 10\\n')
    (out/'final.dcp.ok').write_text('committed')
''')
            tool.chmod(0o755)
            output = root/'results'
            cmd = [sys.executable, str(SCRIPTS/'timing_matrix.py'), '--project', str(project), '--output', str(output),
                   '--vivado', str(tool), '--mhz', '100', '125', '--synthesis', 'current', 'defaults',
                   '--implementation', 'current', 'extra_timing', '--policy', 'exhaustive']
            failed = subprocess.run(cmd, text=True, capture_output=True, timeout=20)
            self.assertNotEqual(failed.returncode, 0, failed.stdout)
            self.assertTrue((root/'failed').exists(), failed.stderr)
            # Original edits after interruption must not enter the frozen experiment.
            rtl.write_text('later RTL edit')
            resumed = subprocess.run(cmd, text=True, capture_output=True, timeout=20)
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            with (output/'matrix_summary.csv').open() as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(len(rows), 8)
            self.assertTrue(all(r['execution'] == 'complete' and r['timing'] == 'violated' for r in rows))
            self.assertEqual(len({(r['synthesis'], r['implementation'], r['mhz']) for r in rows}), 8)
            trace = (root/'trace').read_text().splitlines()
            self.assertEqual(len([l for l in trace if l.startswith('synth')]), 4)
            self.assertEqual((output/'source_snapshot'/rtl.relative_to(root/'repo')).read_text(), 'original RTL')
            # Recovery also works from the copied code, independent of the worktree scripts.
            frozen = cmd.copy()
            frozen[1] = str(output/'code/timing_matrix.py')
            complete = subprocess.run(frozen, text=True, capture_output=True, timeout=20)
            self.assertEqual(complete.returncode, 0, complete.stderr)
            self.assertEqual((root/'trace').read_text().splitlines(), trace)
            (output/'recipes/current.tcl').write_text('modified')
            damaged = subprocess.run(cmd, text=True, capture_output=True, timeout=10)
            self.assertNotEqual(damaged.returncode, 0)
            self.assertIn('recipes changed', damaged.stderr)


if __name__ == '__main__':
    unittest.main()
