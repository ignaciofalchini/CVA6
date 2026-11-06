#!/usr/bin/env python3
"""Append-only, SHA-256 evidence archive and readable timing summaries."""
import argparse
import csv
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import tempfile
import time
from timing_sweep import atomic_json, parse_timing


def keep(path):
    return not any(x in {'.Xil', '__pycache__', '.git'} or x.endswith('.cache') or '.partial' in x
                   for x in path.parts) and path.name not in {'.lock', '.matrix.lock'}


def save_file(source, output):
    before = source.stat()
    digest = hashlib.sha256()
    size = 0
    with tempfile.NamedTemporaryFile(dir=output/'objects', delete=False) as target:
        temp = Path(target.name)
        with source.open('rb') as src:
            for block in iter(lambda: src.read(1024*1024), b''):
                target.write(block)
                digest.update(block)
                size += len(block)
        target.flush()
        os.fsync(target.fileno())
    after = source.stat()
    # Do not archive a checkpoint while it is still being written. Logs may be live.
    if source.suffix == '.dcp' and (before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns):
        temp.unlink()
        return None
    sha = digest.hexdigest()
    dest = output/'objects'/sha
    if dest.exists():
        temp.unlink()
    else:
        temp.replace(dest)
    return dict(sha256=sha, bytes=size, captured_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                source_mtime_ns=after.st_mtime_ns, source_size=after.st_size,
                live_snapshot=(before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns))


def write_csv(path, rows):
    if not rows:
        return
    tmp=path.with_suffix('.partial')
    with tmp.open('w', newline='') as out:
        writer=csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    tmp.replace(path)


def seconds(hms):
    h,m,s=map(float,hms.split(':'))
    return h*3600+m*60+s


def reports(runs, output):
    phases=[]
    points={}
    synthesized=[]
    pattern=re.compile(r'^(synth_design|opt_design|place_design|phys_opt_design|route_design): Time \(s\): cpu = ([\d:]+) ; elapsed = ([\d:]+).*?peak = ([\d.]+)', re.M)
    for run in runs:
        summary=run/'matrix_summary.csv'
        if summary.exists():
            with summary.open() as src:
                for row in csv.DictReader(src):
                    key=(row['mhz'],row['synthesis'],row['implementation'])
                    points[key]=dict(source_run=run.name, **row)
        for log in run.rglob('*.log'):
            rel=log.relative_to(run)
            if not keep(rel): continue
            is_impl=log.name=='console.log' and 'experiments' in rel.parts
            is_synth=log.name=='runme.log' and any(x.endswith('.runs') for x in rel.parts)
            if not (is_impl or is_synth): continue
            text=log.read_text(errors='replace')
            for i,match in enumerate(pattern.finditer(text),1):
                command,cpu,elapsed,memory=match.groups()
                phases.append(dict(source_run=run.name, source_log=str(rel), ordinal=i, command=command,
                                   elapsed_hms=elapsed, elapsed_seconds=seconds(elapsed), cpu_seconds=seconds(cpu),
                                   vivado_peak_mb=float(memory)))
        candidates=list(run.glob('synthesis/*/*MHz/synthesis_timing.rpt'))
        candidates+=list(run.glob('recovery/synthesis_reconstructed/timing_summary.rpt'))
        for report in candidates:
            metrics=parse_timing(report.read_text(errors='replace'))
            synthesized.append(dict(source_run=run.name, report=str(report.relative_to(run)),
                                    reconstructed='recovery' in report.relative_to(run).parts,
                                    wns_ns=metrics.get('wns_ns',''), tns_ns=metrics.get('tns_ns',''),
                                    whs_ns=metrics.get('whs_ns',''), ths_ns=metrics.get('ths_ns',''),
                                    interpretation='Estimated post-synthesis timing, not post-route signoff'))
    write_csv(output/'timing_results.csv',list(points.values()))
    write_csv(output/'phase_times.csv',phases)
    write_csv(output/'synthesis_timing.csv',synthesized)
    text=['CVA6 KR260 — Evidencias de pruebas de timing',
          'Actualizado: '+time.strftime('%Y-%m-%d %H:%M:%S %z'), '',
          'Objetivo: mayor frecuencia probada que cumpla timing post-route.',
          'Un proceso completado no implica timing cumplido.',
          'Los tiempos de CPU, de ejecución de cada etapa y de espera entre corridas son distintos.',
          'Las métricas de síntesis usan retardos estimados. Los reportes reconstruidos están identificados.', '',
          'Resultados finales disponibles:']
    for row in points.values():
        text.append(f"{row['mhz']} MHz | {row['synthesis']} / {row['implementation']} | WNS={row['wns_ns']} ns | TNS={row['tns_ns']} ns | {row['timing']} | {float(row['seconds'])/60:.1f} min implementación")
    text += ['', 'Archivos:',
             'timing_results.csv: puntos de implementación terminados, sin duplicar el piloto importado.',
             'phase_times.csv: tiempos y picos de memoria extraídos de logs; el origen de cada fila está registrado.',
             'synthesis_timing.csv: métricas estimadas de síntesis disponibles.',
             'index.json: rutas originales, versión actual y versiones históricas por SHA-256.',
             'objects/: contenido archivado por hash; nunca se sobrescribe una versión anterior.',
             '', 'Ejemplo para recuperar un archivo: buscar su ruta en index.json y copiar objects/<sha256>.',
             'Los originales permanecen en sus carpetas de corrida. Se omiten caches y archivos temporales en escritura.',
             'Este archivo está en el mismo disco que los originales: no es una copia ante una falla del disco.']
    tmp=output/'RESUMEN.partial'; tmp.write_text('\n'.join(text)+'\n'); tmp.replace(output/'RESUMEN.txt')


def snapshot(runs, output):
    index_path=output/'index.json'
    index=json.loads(index_path.read_text()) if index_path.exists() else dict(schema=1, files={})
    captured=0; errors=[]
    for run in runs:
        for source in run.rglob('*'):
            if not source.is_file() or not keep(source.relative_to(run)): continue
            try:
                stat=source.stat()
                key=str(source)
                entry=index['files'].get(key,dict(versions=[]))
                last=entry['versions'][-1] if entry['versions'] else {}
                if last.get('source_mtime_ns')==stat.st_mtime_ns and last.get('source_size')==stat.st_size:
                    continue
                saved=save_file(source,output)
                if saved is None: continue
                if not last or last['sha256'] != saved['sha256']:
                    entry['versions'].append(saved); captured+=1
                else:
                    entry['versions'][-1].update(saved)
                index['files'][key]=entry
            except (OSError, ValueError) as exc:
                errors.append(dict(source=str(source),error=str(exc)))
    index['updated_at']=time.strftime('%Y-%m-%dT%H:%M:%S%z')
    atomic_json(index_path,index)
    reports(runs,output)
    atomic_json(output/'archive_state.json',dict(updated_at=index['updated_at'],captured_versions=captured,
                                               tracked_paths=len(index['files']),errors=errors))
    print(f"Archived {captured} versions; {len(index['files'])} paths; {len(errors)} errors",flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--watch',action='store_true')
    p.add_argument('--interval',type=int,default=60)
    a=p.parse_args()
    runs=[r.resolve() for r in a.run]; out=a.output.resolve()
    if any(out==r or r in out.parents for r in runs): p.error('Archive output must be outside run directories')
    if a.interval<10:p.error('Use an interval of at least 10 seconds')
    out.mkdir(parents=True,exist_ok=True); (out/'objects').mkdir(exist_ok=True)
    lock=(out/'.archive.lock').open('w'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stopped=[False]
    def stop(*args): stopped[0]=True
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,stop)
    while True:
        snapshot(runs,out)
        if not a.watch or stopped[0]: break
        for _ in range(a.interval):
            if stopped[0]:break
            time.sleep(1)
        if stopped[0]:break


if __name__=='__main__':main()
