#!/usr/bin/env python3
"""Sequential timing sweep with frozen inputs and committed stage recovery."""
import argparse
import csv
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

SCRIPTS = Path(__file__).resolve().parent
PROJECT = SCRIPTS.parent / 'ariane_kr260_debug/ariane_kr260_debug.xpr'
FREQUENCIES = [100, 125, 150, 175, 200, 225, 250, 275, 300]
REPORTS = ['clocks', 'route_status', 'timing_summary', 'check_timing', 'utilization', 'drc']


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, data):
    temp = path.with_suffix(path.suffix + '.partial')
    with temp.open('w') as out:
        json.dump(data, out, indent=2)
        out.flush()
        os.fsync(out.fileno())
    temp.replace(path)


def summary(output, rows):
    temp = output / 'summary.csv.partial'
    with temp.open('w', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        out.flush()
        os.fsync(out.fileno())
    temp.replace(output / 'summary.csv')


def parse_timing(report):
    match = re.search(r'WNS\(ns\).*?\n\s*-+[^\n]*\n\s*([^\n]+)', report, re.S)
    if not match:
        return {}
    values = match.group(1).split()
    indices = dict(wns_ns=0, tns_ns=1, whs_ns=4, ths_ns=5, wpws_ns=8, tpws_ns=9)
    try:
        metrics = {key: float(values[index]) for key, index in indices.items()}
        if not all(math.isfinite(v) for v in metrics.values()):
            return {}
        metrics['timing'] = 'met' if all(metrics[k] >= 0 for k in ('wns_ns', 'whs_ns', 'wpws_ns')) else 'violated'
        return metrics
    except (ValueError, IndexError):
        return {}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint', type=Path, help='Optional standalone linked netlist; default exports current project synth_1 with its IPs')
    p.add_argument('--project', type=Path, default=PROJECT, help='Project recorded as provenance; never modified')
    p.add_argument('--clock', default='clk_pl_0', help='Exact primary clock name')
    p.add_argument('--mhz', type=float, nargs='+', default=FREQUENCIES)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--vivado', default='/home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vivado/bin/vivado')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--implementation-recipe', type=Path, help='Tcl recipe exported from an isolated Vivado implementation run')
    a = p.parse_args()
    if any(not math.isfinite(f) or f <= 0 for f in a.mhz):
        p.error('Frequencies must be positive finite numbers')
    a.project = a.project.resolve()
    if a.checkpoint:
        a.checkpoint = a.checkpoint.resolve()
    a.output = a.output.resolve()
    executable = shutil.which(a.vivado)
    if not executable:
        p.error(f'Vivado executable not found: {a.vivado}')
    script = SCRIPTS / 'timing_sweep.tcl'
    prepare = SCRIPTS / 'prepare_timing_sweep.tcl'
    config = dict(schema=3, project=str(a.project), source_checkpoint=str(a.checkpoint) if a.checkpoint else None,
                  clock=a.clock, mhz=sorted(set(a.mhz)), vivado=executable,
                  vivado_sha256=sha256(executable), tcl_sha256=sha256(script),
                  runner_sha256=sha256(__file__), prepare_sha256=sha256(prepare))
    snapshot = a.output / 'inputs/synth.dcp'
    recipe = a.implementation_recipe.resolve() if a.implementation_recipe else None
    config['recipe_sha256'] = sha256(recipe) if recipe else None
    def command(f, dest):
        cmd = [executable, '-mode', 'batch', '-nojournal', '-log', str(dest / 'vivado.log'),
                '-source', str(script), '-tclargs', str(snapshot), a.clock, str(f), str(dest)]
        if recipe:
            cmd.append(str(snapshot.parent / 'implementation.tcl'))
        return cmd
    if a.dry_run:
        if a.checkpoint is None:
            print(json.dumps([executable, '-mode', 'batch', '-source', str(prepare), '-tclargs', str(a.project), str(snapshot)]))
        for f in config['mhz']:
            print(json.dumps(command(f, a.output / f'{f:g}MHz')))
        return
    a.output.mkdir(parents=True, exist_ok=True)
    with (a.output / '.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            p.error('Another runner is using this output directory')
        manifest_path = a.output / 'manifest.json'
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            if manifest['config'] != config:
                p.error('Configuration/scripts changed; use a new output directory or the original scripts')
            if not snapshot.is_file() or sha256(snapshot) != manifest['checkpoint_sha256']:
                p.error('Frozen checkpoint is missing or changed; refusing unsafe recovery')
        else:
            # Do not adopt orphan checkpoints from a different or uncommitted run.
            if any(a.output.glob('*MHz/*.dcp')):
                p.error('Checkpoints without manifest; select a new output directory')
            snapshot.parent.mkdir(exist_ok=True)
            partial = snapshot.with_name('synth.partial.dcp')
            if a.checkpoint:
                before = sha256(a.checkpoint)
                shutil.copyfile(a.checkpoint, partial)
                if sha256(partial) != before or sha256(a.checkpoint) != before:
                    p.error('Source checkpoint changed during snapshot')
            else:
                print('Exporting current project synthesis with linked IPs', flush=True)
                with (snapshot.parent / 'prepare_console.log').open('w') as log:
                    rc = subprocess.run([executable, '-mode', 'batch', '-nojournal', '-log', str(snapshot.parent / 'prepare_vivado.log'),
                                         '-source', str(prepare), '-tclargs', str(a.project), str(partial)],
                                        cwd=snapshot.parent, stdout=log, stderr=subprocess.STDOUT).returncode
                if rc != 0 or not partial.is_file():
                    p.error('Project preparation failed; inspect inputs/prepare_console.log')
                before = sha256(partial)
            partial.replace(snapshot)
            # Keep the exact recovery code even if the working tree changes later.
            for code in (Path(__file__).resolve(), script, prepare):
                shutil.copyfile(code, snapshot.parent / code.name)
            if recipe:
                shutil.copyfile(recipe, snapshot.parent / 'implementation.tcl')
            provenance = {}
            paths = [a.project, a.project.parent / 'ariane_kr260_debug.srcs/sources_1/bd/kr260_ps_ddr_bd/kr260_ps_ddr_bd.bd',
                     a.project.parent / 'ariane_kr260_debug.runs/synth_1/kr260_top.tcl',
                     SCRIPTS.parent / 'constraints/kr260.xdc']
            for path in paths:
                if path.is_file():
                    dest = snapshot.parent / f'{len(provenance):02d}_{path.name}'
                    shutil.copyfile(path, dest)
                    provenance[str(path)] = dict(sha256=sha256(dest), snapshot=dest.name)
            manifest = dict(config=config, checkpoint_sha256=before, provenance=provenance,
                            created=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
            atomic_json(manifest_path, manifest)
        if recipe and sha256(snapshot.parent / 'implementation.tcl') != config['recipe_sha256']:
            p.error('Frozen implementation recipe changed')
        state = a.output / 'state.json'
        rows = []
        child = None
        stopped = [None]
        def stop(signum, frame):
            stopped[0] = signum
            if child is not None and child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, stop)
        # Reconstruct summary from completed results before doing any new work.
        cached = []
        for f in config['mhz']:
            result = a.output / f'{f:g}MHz/result.json'
            if result.exists():
                cached.append(json.loads(result.read_text()))
        if cached:
            summary(a.output, cached)
        for f in config['mhz']:
            dest = a.output / f'{f:g}MHz'
            dest.mkdir(exist_ok=True)
            result = dest / 'result.json'
            previous = json.loads(result.read_text()) if result.exists() else None
            reports_exist = all((dest / f'{name}.rpt').is_file() for name in REPORTS)
            if previous and previous['execution'] == 'complete' and reports_exist:
                row = previous
            else:
                if stopped[0]:
                    break
                attempts = dest / 'attempts'
                attempts.mkdir(exist_ok=True)
                attempt = time.time_ns()
                for name in ('vivado.log', 'console.log'):
                    if (dest / name).exists():
                        (dest / name).replace(attempts / f'{attempt}_{name}')
                started = time.monotonic()
                atomic_json(state, dict(status='running', mhz=f, pid=os.getpid(), directory=str(dest)))
                print(f'Starting/resuming {f:g} MHz', flush=True)
                with (dest / 'console.log').open('w') as log:
                    child = subprocess.Popen(command(f, dest), cwd=dest, stdout=log,
                                             stderr=subprocess.STDOUT, start_new_session=True)
                    # A stop can arrive during process creation.
                    if stopped[0]:
                        stop(stopped[0], None)
                    rc = child.wait()
                    child = None
                row = dict(mhz=f, execution='failed', seconds=round(time.monotonic()-started, 1),
                           returncode=rc, wns_ns='', tns_ns='', whs_ns='', ths_ns='', wpws_ns='', tpws_ns='',
                           timing='unknown', constraints='review_reports')
                reports_exist = all((dest / f'{name}.rpt').is_file() for name in REPORTS)
                if stopped[0]:
                    row['execution'] = 'interrupted'
                elif rc == 0 and reports_exist and (dest / 'final.dcp.ok').exists():
                    row['execution'] = 'complete'
                    row.update(parse_timing((dest / 'timing_summary.rpt').read_text()))
                atomic_json(result, row)
            rows.append(row)
            # Include previous later-frequency results even when an early retry fails.
            remaining = [r for r in cached if r['mhz'] not in {r['mhz'] for r in rows}]
            summary(a.output, rows + remaining)
            print(f'{f:g} MHz: {row["execution"]}, timing={row["timing"]}', flush=True)
            # Stop on infrastructure/run failures; a timing violation is a valid result.
            if row['execution'] != 'complete' or stopped[0]:
                break
        status = 'interrupted' if stopped[0] else ('complete' if len(rows) == len(config['mhz']) and all(r['execution'] == 'complete' for r in rows) else 'failed')
        atomic_json(state, dict(status=status, pid=os.getpid(), finished=time.strftime('%Y-%m-%dT%H:%M:%S%z')))
        if status != 'complete':
            raise SystemExit(128 + stopped[0] if stopped[0] else 1)


if __name__ == '__main__':
    main()
