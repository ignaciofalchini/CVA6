#!/usr/bin/env python3
"""Evidence-driven timing campaign. Resume with the same output and frozen code."""
import argparse, csv, fcntl, hashlib, json, os, shutil, signal, subprocess, sys, time
from pathlib import Path
from timing_sweep import atomic_json, sha256, REPORTS
from timing_matrix import ignored, relocate, inventory, closure
SCRIPTS=Path(__file__).resolve().parent
VIVADO='/home/nachofalchi/data/fpga-work/Xilinx/2026.1/Vivado/bin/vivado'
FILES=['timing_night.py','timing_matrix.py','timing_sweep.py','timing_sweep.tcl','timing_matrix_project.tcl','prepare_timing_sweep.tcl']

def ranking(rows):
    return sorted((r for r in rows if r.get('execution')=='complete'), key=lambda r:(float(r['wns_ns']),float(r['tns_ns'])),reverse=True)

def jobs_for_winner(rows):
    ranked=ranking(rows)
    return [(ranked[0]['synthesis'],i) for i in ('netdelay_high','wl_block','explore_postroute')] if ranked else []

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seed',type=Path,required=True)
    a=p.parse_args();root=a.output.resolve();seed=a.seed.resolve();root.mkdir(parents=True,exist_ok=True)
    lock=(root/'.night.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    frozen=Path('/home/nachofalchi/data/fpga-work/archivo/timing-matrix/pilot_100mhz/source_snapshot')
    sm=json.loads((seed/'matrix_manifest.json').read_text())
    if inventory(frozen)!=sm['files']:raise RuntimeError('Frozen HDL source inventory mismatch')
    code=root/'code';code.mkdir(exist_ok=True)
    if not (root/'manifest.json').exists():
        for name in FILES:shutil.copy2(SCRIPTS/name,code/name)
        shutil.copy2(seed/'strategy_evaluation.json',root/'strategy_evaluation.json')
        atomic_json(root/'manifest.json',dict(frequencies=[100,125,150,175,200],seed=str(seed),source=str(frozen),source_inventory=sm['files'],code={n:sha256(code/n) for n in FILES},threads=4,policy='screen 3 synthesis baselines, test 3 implementation alternatives on best synthesis, cross best implementation on runner-up; continue every frequency'))
    manifest=json.loads((root/'manifest.json').read_text())
    if any(sha256(code/n)!=v for n,v in manifest['code'].items()):raise RuntimeError('Frozen campaign code mismatch')
    child=[None];stopped=[False]
    def stop(sig,frame):
        stopped[0]=True
        if child[0] and child[0].poll() is None:
            try:os.killpg(child[0].pid,signal.SIGTERM)
            except ProcessLookupError:pass
    for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,stop)
    def run(cmd,log):
        if stopped[0]:raise InterruptedError()
        if shutil.disk_usage(root).free<2*1024**3:raise RuntimeError('Disk guard: less than 2 GiB free; data retained, resume after freeing space')
        log.parent.mkdir(parents=True,exist_ok=True)
        if log.exists():log.rename(log.with_name(log.name+'.'+str(time.time_ns())))
        with log.open('w') as stream, (root/'resources.jsonl').open('a') as telemetry:
            child[0]=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,cwd=log.parent,start_new_session=True)
            while child[0].poll() is None:
                # Per-process CPU, RSS and thread counts plus memory/swap and disk samples.
                ps=subprocess.run(['ps','-eo','pid,ppid,pcpu,rss,nlwp,comm'],capture_output=True,text=True).stdout
                sample=dict(time=time.time(),command=cmd,meminfo=Path('/proc/meminfo').read_text(),vmstat=Path('/proc/vmstat').read_text(),processes='\n'.join(x for x in ps.splitlines() if 'vivado' in x or 'python' in x),disk_free=shutil.disk_usage(root).free)
                telemetry.write(json.dumps(sample)+'\n');telemetry.flush()
                time.sleep(5)
            rc=child[0].returncode;child[0]=None
        if stopped[0]:raise InterruptedError()
        return rc
    relative=Path(sm['relative_project']);project=frozen/relative
    recipes=root/'recipes'
    if not (recipes/'netdelay_high.tcl').exists():
        clone=root/'preflight_source'
        if not clone.exists():shutil.copytree(frozen,clone,ignore=ignored);relocate(clone,frozen,clone)
        rc=run([VIVADO,'-mode','batch','-nojournal','-log',str(root/'preflight.vivado.log'),'-source',str(code/'timing_matrix_project.tcl'),'-tclargs','preflight',str(clone/relative),str(clone),str(recipes),'current','100'],root/'preflight.log')
        if rc:raise RuntimeError('Preflight failed; inspect preflight.log')
        shutil.copy2(seed/'recipes/current.tcl',recipes/'current.tcl')
        atomic_json(root/'recipes_manifest.json',{x.name:sha256(x) for x in recipes.glob('*.tcl')})
    expected=json.loads((root/'recipes_manifest.json').read_text())
    if any(sha256(recipes/n)!=v for n,v in expected.items()):raise RuntimeError('Recipe changed')
    # Explicit index of all completed historical experiments, including directed branches.
    history=[]
    for result in seed.rglob('result.json'):
        try:
            row=json.loads(result.read_text())
            if row.get('execution')=='complete':history.append(dict(path=str(result.parent),result=row))
        except (OSError,ValueError):pass
    atomic_json(root/'historical_results.json',history)
    all_rows=[]
    def save_summary():
        atomic_json(root/'results.json',all_rows)
        if all_rows:
            keys=sorted(set().union(*(r.keys() for r in all_rows)))
            with (root/'summary.csv').open('w') as f:
                w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(all_rows)
    def evaluate(synth,impl,mhz):
        dest=root/'experiments'/synth/f'{mhz}MHz'/impl;folder=dest/f'{mhz}MHz'
        atomic_json(root/'state.json',dict(status='running',mhz=mhz,synthesis=synth,implementation=impl))
        # Cached results remain in their original provenance; never rewrite old manifests.
        cached=seed/'experiments'/synth/f'{mhz}MHz'/impl/f'{mhz}MHz'
        for candidate in (folder,cached):
            if (candidate/'result.json').exists() and all((candidate/f'{n}.rpt').exists() for n in REPORTS):
                row=json.loads((candidate/'result.json').read_text())
                if row['execution']=='complete':
                    row.update(synthesis=synth,implementation=impl,path=str(candidate),reused=candidate==cached)
                    all_rows.append(row);save_summary();return row
        pair=root/'synthesis'/synth/f'{mhz}MHz';checkpoint=pair/'linked_synth.dcp';done=pair/'synthesis.json'
        existing=seed/'synthesis'/synth/f'{mhz}MHz'
        if not done.exists() and (existing/'synthesis.json').exists():
            info=json.loads((existing/'synthesis.json').read_text())
            if sha256(existing/'linked_synth.dcp')!=info['sha256']:raise RuntimeError('Cached synthesis hash mismatch')
            pair.mkdir(parents=True,exist_ok=True);shutil.copy2(existing/'linked_synth.dcp',checkpoint)
            atomic_json(done,{**info,'reused_from':str(existing)})
        if not done.exists():
            pair.mkdir(parents=True,exist_ok=True);clone=pair/'source'
            if not clone.exists():shutil.copytree(frozen,clone,ignore=ignored);relocate(clone,frozen,clone)
            start=time.monotonic();partial=pair/'linked_synth.partial.dcp'
            rc=run([VIVADO,'-mode','batch','-nojournal','-log',str(pair/'synthesis.vivado.log'),'-source',str(code/'timing_matrix_project.tcl'),'-tclargs','synth',str(clone/relative),str(clone),str(pair/'recipes'),synth,str(mhz),str(partial)],pair/'synthesis.log')
            if rc or not partial.exists():
                row=dict(mhz=mhz,synthesis=synth,implementation=impl,execution='synthesis_failed',returncode=rc,path=str(pair));all_rows.append(row);save_summary();return row
            partial.rename(checkpoint);atomic_json(done,dict(sha256=sha256(checkpoint),seconds=time.monotonic()-start))
        if sha256(checkpoint)!=json.loads(done.read_text())['sha256']:raise RuntimeError('Synthesis checkpoint changed')
        cmd=[sys.executable,'-u',str(code/'timing_sweep.py'),'--project',str(project),'--checkpoint',str(checkpoint),'--clock','clk_pl_0','--mhz',str(mhz),'--implementation-recipe',str(recipes/f'{impl}.tcl'),'--vivado',VIVADO,'--output',str(dest)]
        rc=run(cmd,dest/'runner.log')
        row=json.loads((folder/'result.json').read_text()) if (folder/'result.json').exists() else dict(mhz=mhz,execution='failed',returncode=rc)
        row.update(synthesis=synth,implementation=impl,path=str(folder),reused=False)
        if row['execution']=='complete':
            verdict,problems=closure(folder);row['signoff']=verdict;row['signoff_problems']=';'.join(problems)
        all_rows.append(row);save_summary();return row
    try:
        for mhz in manifest['frequencies']:
            baseline=[evaluate(s,'current',mhz) for s in ('defaults','carry','alternate')]
            ranked=ranking(baseline)
            if not ranked:continue
            trials=[evaluate(s,i,mhz) for s,i in jobs_for_winner(baseline)]
            best=ranking(baseline+trials)[0]
            if len(ranked)>1 and best['implementation']!='current':evaluate(ranked[1]['synthesis'],best['implementation'],mhz)
            atomic_json(root/f'frequency_{mhz}.json',dict(status='tested',best=ranking([r for r in all_rows if r['mhz']==mhz])[0],note='Final timing closure requires signoff review; advance to next requested frequency even if timing fails.'))
        atomic_json(root/'state.json',dict(status='complete',finished=time.time()))
    except InterruptedError:atomic_json(root/'state.json',dict(status='interrupted',time=time.time()));raise SystemExit(143)
    except Exception as exc:
        atomic_json(root/'state.json',dict(status='blocked_by_error',error=str(exc),time=time.time()));raise

if __name__=='__main__':main()
