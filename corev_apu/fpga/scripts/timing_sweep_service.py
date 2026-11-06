#!/usr/bin/env python3
"""Start/status/stop/resume a logout-independent timing sweep on the Linux host."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from timing_sweep import PROJECT

RUNNER = Path(__file__).with_name('timing_sweep.py').resolve()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['start', 'resume', 'status', 'stop'])
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--mhz', type=float, nargs='+', help='Only for start; runner defaults otherwise')
    p.add_argument('--matrix', action='store_true', help='Start synthesis/implementation strategy matrix')
    p.add_argument('--synthesis', nargs='+', choices=['current', 'defaults', 'carry'])
    p.add_argument('--implementation', nargs='+', choices=['current', 'explore_postroute', 'extra_timing'])
    p.add_argument('--policy', choices=['progressive', 'exhaustive'])
    p.add_argument('--seed-run', type=Path)
    p.add_argument('--wait-for-seed', action='store_true')
    a = p.parse_args()
    output = a.output.resolve()
    unit = 'cva6-timing-' + hashlib.sha256(str(output).encode()).hexdigest()[:12]
    launch = output / 'launch.json'
    if a.action == 'status':
        for name in ('state.json', 'search_progress.json', 'summary.csv', 'matrix_summary.csv'):
            path = output / name
            if path.exists():
                print(path.read_text())
        for folder in sorted(output.glob('*MHz')):
            stages = [s for s in ('constrained', 'optimized', 'placed', 'physopt', 'routed', 'final')
                      if (folder / (s + '.dcp.ok')).is_file()]
            if stages:
                print(f'{folder.name}: last committed stage = {stages[-1]}')
        subprocess.run(['systemctl', '--user', '--no-pager', 'status', unit])
        return
    if a.action == 'stop':
        subprocess.run(['systemctl', '--user', 'stop', unit], check=True)
        return
    if a.action == 'resume' and (any(x is not None for x in (a.mhz, a.synthesis, a.implementation, a.policy, a.seed_run)) or a.wait_for_seed):
        p.error('Resume uses the stored frequencies and strategies; omit new selections')
    if not a.matrix and (a.synthesis or a.implementation):
        p.error('Strategy selections require --matrix')
    if not a.matrix and (a.policy or a.seed_run or a.wait_for_seed):
        p.error('Progressive search selections require --matrix')
    # Linger is a host prerequisite, never assume tmux/nohup survives a full logout.
    linger = subprocess.run(['loginctl', 'show-user', str(os.getuid()), '-p', 'Linger', '--value'],
                            text=True, capture_output=True)
    if linger.returncode or linger.stdout.strip() != 'yes':
        p.error('Linger could not be verified. On the host enable it with: loginctl enable-linger "$USER"')
    if a.action == 'start':
        runner = RUNNER.with_name('timing_matrix.py') if a.matrix else RUNNER
        command = [sys.executable, '-u', str(runner), '--output', str(output), '--project', str(PROJECT)]
        if not a.matrix:
            command += ['--clock', 'clk_pl_0']
        if a.mhz:
            command += ['--mhz', *map(str, a.mhz)]
        for name in ('synthesis', 'implementation'):
            if getattr(a, name):
                command += ['--' + name, *getattr(a, name)]
        if a.policy:
            command += ['--policy', a.policy]
        if a.seed_run:
            command += ['--seed-run', str(a.seed_run.resolve())]
        if a.wait_for_seed:
            command += ['--wait-for-seed']
        if launch.exists() and json.loads(launch.read_text()) != command:
            p.error('Existing launch configuration differs; use resume or another output directory')
        output.mkdir(parents=True, exist_ok=True)
        # Verify runner arguments and executable without starting implementation.
        subprocess.run(command + ['--dry-run'], check=True, stdout=subprocess.DEVNULL)
        temp = launch.with_suffix('.partial')
        temp.write_text(json.dumps(command, indent=2))
        temp.replace(launch)
    else:
        if not launch.exists():
            p.error('No launch.json; use start for a new run')
        command = json.loads(launch.read_text())
        frozen_runner = (output / ('code/' + Path(command[2]).name) if Path(command[2]).name in {'timing_matrix.py', 'timing_night.py'}
                         else output / 'inputs/timing_sweep.py')
        if frozen_runner.is_file():
            command[2] = str(frozen_runner)
    service = ['systemd-run', '--user', '--collect', '--unit=' + unit,
               '--property=Type=exec', '--property=KillMode=control-group',
               '--property=TimeoutStopSec=60', '--property=WorkingDirectory=' + str(output)]
    # Pass only environment needed by Vivado; no credentials are printed.
    for name in ('PATH', 'HOME', 'LANG', 'LD_LIBRARY_PATH', 'XILINX_VIVADO',
                 'XILINXD_LICENSE_FILE', 'LM_LICENSE_FILE'):
        if name in os.environ:
            service.append('--setenv=' + name)
    subprocess.run(service + command, check=True)
    print(f'Unit: {unit}\nResults: {output}\nUse this same helper with status, stop or resume.')


if __name__ == '__main__':
    main()
