#!/usr/bin/env python3
"""Isolated synthesis x implementation x frequency experiments, with recovery."""
import argparse
import csv
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from timing_sweep import PROJECT, FREQUENCIES, REPORTS, atomic_json, sha256, summary

SCRIPTS = Path(__file__).resolve().parent
SYNTH = {'current': 'Current project settings', 'defaults': 'Vivado Synthesis Defaults', 'carry': 'Flow_PerfThresholdCarry'}
IMPL = {'current': 'Current project settings', 'explore_postroute': 'Performance_ExplorePostRoutePhysOpt', 'extra_timing': 'Performance_ExtraTimingOpt'}
EXCLUDE = {'.git', '.Xil', '__pycache__', 'software', 'xilinx'}
TEXT = {'.xpr', '.xml', '.bd', '.xci', '.tcl', '.xdc', '.v', '.sv', '.svh', '.vh', '.vhd', '.vhdl', '.json', '.prj'}


def ignored(path, names):
    return [n for n in names if n in EXCLUDE or n.endswith(('.cache', '.runs', '.sim', '.zip', '.tar.gz', '.tar.zst'))]


def relocate(root, old, new):
    for p in root.rglob('*'):
        if p.is_file() and p.suffix.lower() in TEXT:
            try:
                data = p.read_text()
            except UnicodeDecodeError:
                continue
            changed = data.replace(str(old), str(new))
            if changed != data:
                p.write_text(changed)


def inventory(root):
    return {str(p.relative_to(root)): sha256(p) for p in root.rglob('*')
            if p.is_file() and not any(x == '.Xil' or x.endswith(('.cache', '.runs')) for x in p.relative_to(root).parts)
            and p.suffix not in {'.log', '.jou', '.str'}}


def collect(output):
    rows = []
    for path in sorted(output.glob('experiments/*/*/*/summary.csv')):
        synth, freq, impl = path.parts[-4:-1]
        with path.open() as source:
            for row in csv.DictReader(source):
                rows.append(dict(synthesis=synth, implementation=impl, **row))
    if rows:
        temp = output / 'matrix_summary.csv.partial'
        with temp.open('w', newline='') as out:
            writer = csv.DictWriter(out, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        temp.replace(output / 'matrix_summary.csv')
    return rows


def closure(folder):
    """Advance only on a complete, constrained post-route timing result."""
    result = json.loads((folder/'result.json').read_text())
    if result['execution'] != 'complete':
        return 'review', ['execution_incomplete']
    if result['timing'] == 'violated':
        return 'failed', []
    if result['timing'] != 'met':
        return 'review', ['timing_unknown']
    problems = []
    timing = (folder/'timing_summary.rpt').read_text()
    if 'All user specified timing constraints are met.' not in timing:
        problems.append('timing_signoff_missing')
    checks = (folder/'check_timing.rpt').read_text()
    counts = {name: int(n) for name, n in re.findall(r'checking\s+(\w+)\s+\((\d+)\)', checks)}
    required = {'no_clock', 'unconstrained_internal_endpoints', 'no_input_delay', 'no_output_delay',
                'multiple_clock', 'generated_clocks', 'loops', 'partial_input_delay', 'partial_output_delay', 'latch_loops'}
    if not required.issubset(counts):
        problems.append('constraint_checks_missing')
    problems += [f'{name}={n}' for name, n in counts.items() if n and name != 'constant_clock']
    route = (folder/'route_status.rpt').read_text()
    match = re.search(r'# of nets with routing errors[^:\n]*:\s*(\d+)', route, re.I)
    if not match or int(match[1]):
        problems.append('routing_not_verified')
    drc = (folder/'drc.rpt').read_text()
    if 'Report DRC' not in drc:
        problems.append('drc_report_missing')
    if re.search(r'\|\s*(?:Error|Critical Warning)\s*\|', drc, re.I):
        problems.append('drc_errors_or_critical_warnings')
    # Also reject critical methodology findings in the timing summary.
    if re.search(r'^\S+\s+Critical Warning\s+', timing, re.M):
        problems.append('critical_timing_methodology')
    return ('review', problems) if problems else ('passed', [])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--project', type=Path, default=PROJECT)
    p.add_argument('--mhz', type=float, nargs='+', default=FREQUENCIES)
    p.add_argument('--policy', choices=['progressive', 'exhaustive'], default='progressive')
    p.add_argument('--seed-run', type=Path, help='Reuse the exact frozen sources and completed results of an earlier matrix')
    p.add_argument('--wait-for-seed', action='store_true', help='Wait for that earlier service to finish without interrupting it')
    p.add_argument('--synthesis', choices=list(SYNTH), nargs='+', default=list(SYNTH))
    p.add_argument('--implementation', choices=list(IMPL), nargs='+', default=list(IMPL))
    p.add_argument('--vivado', default='/home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vivado/bin/vivado')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--preflight-only', action='store_true')
    a = p.parse_args()
    import math
    if any(not math.isfinite(f) or f < 100 for f in a.mhz):
        p.error('Frequencies must be finite and at least 100 MHz')
    a.output = a.output.resolve()
    a.project = a.project.resolve()
    if a.seed_run:
        a.seed_run = a.seed_run.resolve()
    executable = shutil.which(a.vivado)
    if not executable:
        p.error('Vivado executable not found')
    files = ['timing_matrix.py', 'timing_matrix_project.tcl', 'timing_sweep.py', 'timing_sweep.tcl', 'prepare_timing_sweep.tcl']
    config = dict(schema=2, project=str(a.project), mhz=sorted(set(a.mhz)), policy=a.policy,
                  seed_run=str(a.seed_run) if a.seed_run else None,
                  synthesis=list(dict.fromkeys(a.synthesis)), implementation=list(dict.fromkeys(a.implementation)),
                  vivado=executable, executable_sha256=sha256(executable),
                  code={n: sha256(SCRIPTS/n) for n in files})
    count = len(config['mhz']) * len(config['synthesis']) * len(config['implementation'])
    print(f'Policy={a.policy}; at most {len(config["mhz"])*len(config["synthesis"])} synthesis jobs, {count} routed experiments', flush=True)
    if a.dry_run:
        print(json.dumps(config, indent=2))
        return
    a.output.mkdir(parents=True, exist_ok=True)
    lock = (a.output/'.matrix.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        p.error('Matrix already running')
    state = a.output/'state.json'
    stopped = [False]
    active = [None]
    def stop(signum, frame):
        stopped[0] = True
        if active[0] is not None and active[0].poll() is None:
            try:
                os.killpg(active[0].pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, stop)
    # Freeze recovery code before waiting, so logout/restart does not depend on
    # later worktree edits. The pilot continues under its original coordinator.
    code = a.output/'code'
    if not (a.output/'matrix_manifest.json').exists():
        code.mkdir(exist_ok=True)
        for name in files:
            target = code/name
            if (SCRIPTS/name).resolve() != target.resolve():
                shutil.copyfile(SCRIPTS/name, target)
    if a.seed_run and not (a.output/'matrix_manifest.json').exists():
        while True:
            seed_state_path = a.seed_run/'state.json'
            seed_state = json.loads(seed_state_path.read_text()) if seed_state_path.exists() else {}
            if seed_state.get('status') == 'complete':
                break
            if not a.wait_for_seed or seed_state.get('status') in {'failed', 'interrupted'}:
                atomic_json(state, dict(status='seed_not_complete', seed=str(a.seed_run), seed_state=seed_state))
                p.error('Seed run is not complete; inspect the pilot before proceeding')
            atomic_json(state, dict(status='waiting_for_seed', seed=str(a.seed_run), seed_state=seed_state))
            unit = 'cva6-timing-' + hashlib.sha256(str(a.seed_run).encode()).hexdigest()[:12]
            check = subprocess.run(['systemctl', '--user', 'is-active', unit], capture_output=True, text=True)
            if check.returncode:
                if seed_state_path.exists() and json.loads(seed_state_path.read_text()).get('status') == 'complete':
                    break
                atomic_json(state, dict(status='seed_not_active', seed=str(a.seed_run), seed_state=seed_state))
                p.error('Seed service is no longer active and has no complete result')
            time.sleep(5)
            if stopped[0]:
                atomic_json(state, dict(status='interrupted', seed=str(a.seed_run)))
                raise SystemExit(143)
    def run(command, log):
        log.parent.mkdir(parents=True, exist_ok=True)
        if log.exists():
            log.replace(log.with_name(f'{log.stem}.{time.time_ns()}{log.suffix}'))
        with log.open('w') as stream:
            active[0] = subprocess.Popen(command, cwd=log.parent, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            if stopped[0]:
                stop(signal.SIGTERM, None)
            rc = active[0].wait()
            active[0] = None
        if rc or stopped[0]:
            atomic_json(state, dict(status='interrupted' if stopped[0] else 'failed', log=str(log)))
            raise SystemExit(143 if stopped[0] else 1)
    def vivado(mode, project, source_root, recipes, profile, mhz, log, checkpoint=None):
        cmd = [executable, '-mode', 'batch', '-nojournal', '-log', str(log.with_suffix('.vivado.log')),
               '-source', str(a.output/'code/timing_matrix_project.tcl'), '-tclargs', mode,
               str(project), str(source_root), str(recipes), profile, str(mhz)]
        if checkpoint:
            cmd.append(str(checkpoint))
        run(cmd, log)
    source_root = a.project.parents[3]
    relative_project = a.project.relative_to(source_root)
    frozen = a.seed_run/'source_snapshot' if a.seed_run else a.output/'source_snapshot'
    manifest_path = a.output/'matrix_manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest['config'] != config:
            p.error('Matrix configuration/code changed; use original frozen code or another output')
        if inventory(frozen) != manifest['files']:
            p.error('Frozen source snapshot changed; refusing mixed-source recovery')
        if {f.name: sha256(f) for f in (a.output/'recipes').glob('*.tcl')} != manifest['recipes']:
            p.error('Frozen implementation recipes changed')
    elif a.seed_run:
        seed_manifest = json.loads((a.seed_run/'matrix_manifest.json').read_text())
        if seed_manifest['config']['project'] != str(a.project):
            p.error('Seed belongs to another project')
        if inventory(frozen) != seed_manifest['files']:
            p.error('Seed source snapshot changed')
        recipes = a.output/'recipes'
        recipes.mkdir(exist_ok=True)
        for name, expected in seed_manifest['recipes'].items():
            source = a.seed_run/'recipes'/name
            if sha256(source) != expected:
                p.error('Seed recipe changed')
            shutil.copyfile(source, recipes/name)
        manifest = dict(config=config, files=seed_manifest['files'], relative_project=seed_manifest['relative_project'],
                        recipes=seed_manifest['recipes'])
        relative_project = Path(manifest['relative_project'])
        atomic_json(manifest_path, manifest)
    else:
        if (a.output/'experiments').exists() or (a.output/'synthesis').exists():
            p.error('Experiments without matrix manifest; choose another output')
        atomic_json(state, dict(status='preparing_snapshot'))
        partial = a.output/'source_snapshot.partial'
        if partial.exists():
            shutil.rmtree(partial)
        partial.mkdir()
        source_hashes = {}
        def copy_source(src, dst):
            expected = sha256(src)
            shutil.copy2(src, dst)
            if sha256(dst) != expected:
                p.error(f'Source changed during snapshot: {src}')
            source_hashes[str(src)] = expected
            return dst
        # Preserve the original directory layout, including generated IP artifacts.
        for name in ('core', 'vendor', 'common', 'config', 'corev_apu'):
            if (source_root/name).is_dir():
                shutil.copytree(source_root/name, partial/name, ignore=ignored,
                                ignore_dangling_symlinks=True, copy_function=copy_source)
        if any(sha256(path) != expected for path, expected in source_hashes.items()):
            p.error('Sources changed during snapshot; retry with stable sources')
        if not (partial/relative_project).is_file():
            p.error('Unsupported project layout')
        relocate(partial, source_root, frozen)
        if frozen.exists():
            # Only a previous incomplete preparation may exist without a manifest.
            if (a.output/'experiments').exists():
                p.error('Experiments without manifest; choose another output')
            shutil.rmtree(frozen)
        partial.replace(frozen)
        vivado('preflight', frozen/relative_project, frozen, a.output/'recipes', 'current', 100,
               a.output/'preflight/console.log')
        manifest = dict(config=config, files=inventory(frozen), relative_project=str(relative_project),
                        recipes={f.name: sha256(f) for f in (a.output/'recipes').glob('*.tcl')})
        atomic_json(manifest_path, manifest)
    if a.preflight_only:
        atomic_json(state, dict(status='preflight_complete'))
        print('Snapshot and strategy recipes ready; no synthesis or routing executed', flush=True)
        return
    collect(a.output)
    progress = dict(policy=a.policy, closed=[], highest_closed_mhz=None, limiting_mhz=None, range_complete=False)
    for mhz in config['mhz']:
        frequency_closed = False
        preferred = progress['closed'][-1] if progress['closed'] else None
        synth_order = sorted(config['synthesis'], key=lambda s: 0 if preferred and s == preferred['synthesis'] else 1)
        for synth in synth_order:
            pair = a.output/'synthesis'/synth/f'{mhz:g}MHz'
            checkpoint = pair/'linked_synth.dcp'
            done = pair/'synthesis.json'
            if a.seed_run and not done.exists():
                source_pair = a.seed_run/'synthesis'/synth/f'{mhz:g}MHz'
                source_done = source_pair/'synthesis.json'
                if source_done.exists():
                    info = json.loads(source_done.read_text())
                    if sha256(source_pair/'linked_synth.dcp') != info['sha256']:
                        p.error('Seed synthesis changed')
                    pair.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source_pair/'linked_synth.dcp', checkpoint)
                    atomic_json(done, {**info, 'imported_from': str(source_pair)})
            if done.exists():
                expected = json.loads(done.read_text())['sha256']
                if not checkpoint.is_file() or sha256(checkpoint) != expected:
                    p.error(f'Committed synthesis checkpoint missing/changed: {pair}')
            else:
                atomic_json(state, dict(status='synthesis', synthesis=synth, mhz=mhz))
                clone = pair/'source'
                if not clone.exists():
                    clone_partial = pair/'source.partial'
                    if clone_partial.exists():
                        shutil.rmtree(clone_partial)
                    pair.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(frozen, clone_partial, ignore=ignored)
                    relocate(clone_partial, frozen, clone)
                    clone_partial.replace(clone)
                partial = pair/'linked_synth.partial.dcp'
                started = time.monotonic()
                vivado('synth', clone/relative_project, clone, pair/'recipes', synth, mhz,
                       pair/'synthesis_console.log', partial)
                if not partial.is_file():
                    p.error('Synthesis returned without checkpoint')
                partial.replace(checkpoint)
                atomic_json(done, dict(sha256=sha256(checkpoint), seconds=time.monotonic()-started))
            impl_order = sorted(config['implementation'], key=lambda s: 0 if preferred and s == preferred['implementation'] else 1)
            for impl in impl_order:
                dest = a.output/'experiments'/synth/f'{mhz:g}MHz'/impl
                if a.seed_run:
                    source_folder = a.seed_run/'experiments'/synth/f'{mhz:g}MHz'/impl/f'{mhz:g}MHz'
                    local_folder = dest/f'{mhz:g}MHz'
                    if (source_folder/'result.json').exists() and not (local_folder/'result.json').exists():
                        row = json.loads((source_folder/'result.json').read_text())
                        if row['execution'] == 'complete' and all((source_folder/f'{r}.rpt').is_file() for r in REPORTS):
                            local_folder.mkdir(parents=True, exist_ok=True)
                            for r in REPORTS:
                                shutil.copyfile(source_folder/f'{r}.rpt', local_folder/f'{r}.rpt')
                            atomic_json(local_folder/'result.json', row)
                            atomic_json(local_folder/'import.json', dict(source=str(source_folder)))
                            summary(dest, [row])
                atomic_json(state, dict(status='implementation', synthesis=synth, implementation=impl, mhz=mhz))
                cmd = [sys.executable, '-u', str(a.output/'code/timing_sweep.py'), '--project', str(frozen/relative_project),
                       '--checkpoint', str(checkpoint), '--clock', 'clk_pl_0', '--mhz', str(mhz),
                       '--implementation-recipe', str(a.output/'recipes'/f'{impl}.tcl'),
                       '--vivado', executable, '--output', str(dest)]
                try:
                    run(cmd, dest/'runner.log')
                finally:
                    collect(a.output)
                if stopped[0]:
                    raise SystemExit(143)
                if a.policy == 'progressive':
                    verdict, problems = closure(dest/f'{mhz:g}MHz')
                    atomic_json(dest/'closure.json', dict(verdict=verdict, problems=problems, mhz=mhz))
                    if verdict == 'review':
                        atomic_json(a.output/'search_progress.json', progress)
                        atomic_json(state, dict(status='needs_review', mhz=mhz, synthesis=synth,
                                                implementation=impl, problems=problems))
                        raise SystemExit(1)
                    if verdict == 'passed':
                        progress['closed'].append(dict(mhz=mhz, synthesis=synth, implementation=impl))
                        progress['highest_closed_mhz'] = mhz
                        frequency_closed = True
                        atomic_json(a.output/'search_progress.json', progress)
                        print(f'Timing closed at {mhz:g} MHz with {synth}/{impl}; advancing', flush=True)
                        break
            if a.policy == 'progressive' and frequency_closed:
                break
        if a.policy == 'progressive' and not frequency_closed:
            progress['limiting_mhz'] = mhz
            atomic_json(a.output/'search_progress.json', progress)
            atomic_json(state, dict(status='frequency_limit', mhz=mhz, highest_closed_mhz=progress['highest_closed_mhz']))
            print(f'No selected strategy closed at {mhz:g} MHz; stopping', flush=True)
            return
    progress['range_complete'] = True
    atomic_json(a.output/'search_progress.json', progress)
    atomic_json(state, dict(status='complete'))


if __name__ == '__main__':
    main()
