"""Host-collector adversarial acceptance through real public CLI and containers.
Author: Ethan. No provider mocks or imported implementation internals.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import sqlite3
import subprocess
import sys
import time
import threading
import signal
import hashlib

parser = argparse.ArgumentParser()
parser.add_argument('--root', required=True, type=Path)
parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1])
parser.add_argument('--cli', type=Path, default=Path('.venv/bin/abl'))
parser.add_argument('--observe', action='store_true', help='Record old behavior without requiring repaired contracts')
a = parser.parse_args()
a.root = a.root.resolve(); a.source = a.source.resolve(); a.cli = a.cli.resolve()
a.root.mkdir(parents=True, exist_ok=True)
if (a.root/'source').exists(): raise SystemExit('Use a fresh root')
copy = a.root/'source'
shutil.copytree(a.source/'abl', copy/'abl', ignore=shutil.ignore_patterns('__pycache__','static'))
shutil.copytree(a.source/'corpus', copy/'corpus', ignore=shutil.ignore_patterns('__pycache__'))
env = dict(os.environ, PYTHONPATH=str(copy))
reference = copy/'corpus/bugfix-rounding/reference.json'
original = json.loads(reference.read_text())
results = []

def cli(args, timeout=90):
    return subprocess.run([str(a.cli), *args],env=env,cwd=copy,text=True,capture_output=True,timeout=timeout)

def run(name, code, expected, attempts=1):
    for attempt in range(attempts):
        actions=[{'tool':'shell','arguments':{'command':'python -c '+shlex.quote(code)}}, *original]
        reference.write_text(json.dumps(actions))
        root=a.root/(name+'-'+str(attempt))
        sizes=[]; stop=threading.Event()
        def observe_sizes():
            while not stop.wait(.002):
                for f in root.glob('artifacts/*/agent/workspace.tar*'):
                    try: sizes.append(f.stat().st_size)
                    except FileNotFoundError: pass
        monitor=threading.Thread(target=observe_sizes,daemon=True); monitor.start()
        start=time.monotonic(); p=cli(['run','--root',str(root),'--task','bugfix-rounding'])
        stop.set(); monitor.join()
        db=sqlite3.connect(root/'results.sqlite3')
        t=json.loads(db.execute('select data from trials').fetchone()[0]); db.close()
        events=[json.loads(x) for x in Path(t['artifact_dir'],'trace.jsonl').read_text().splitlines()]
        artifact=Path(t['artifact_dir'],'agent/workspace.tar')
        tool=[e for e in events if e['kind']=='tool' and e['tool']=='shell']
        result=tool[0]['result'] if tool else None
        # Retain precise byte counts, not megabytes of repeated data in evidence.
        compact=None if result is None else {k:v for k,v in result.items() if k not in ('stdout','stderr')}
        if compact is not None: compact.update(stdout_retained_bytes=len(result.get('stdout','').encode()),stderr_retained_bytes=len(result.get('stderr','').encode()))
        record={'case':name,'attempt':attempt,'cli_exit':p.returncode,'elapsed_seconds':time.monotonic()-start,
            'trial_id':t['id'],'status':t['status'],'failure_category':t['failure_category'],
            'tool_calls':t['tool_calls'],'failed_tool_calls':t['failed_tool_calls'],
            'artifact_bytes':artifact.stat().st_size if artifact.exists() else 0,'tool_result':compact,
            'cleanup_errors':t['cleanup_errors'],'artifact_metadata':t.get('artifact'),
            'trace_kinds':[e['kind'] for e in events],'observed_peak_archive_bytes':max(sizes,default=0)}
        results.append(record)
        (a.root/'results.json').write_text(json.dumps(results,indent=2))
        print(json.dumps(record),flush=True)
        if a.observe: continue
        assert not t['cleanup_errors'],record
        assert max(sizes,default=0)<=64000000,record
        if artifact.exists(): assert hashlib.sha256(artifact.read_bytes()).hexdigest()==t['artifact']['sha256'],record
        if expected=='truncated':
            assert t['status']=='PASS' and p.returncode==0,record
            assert result['stdout_bytes']==400001 and result['stdout_truncated'],record
            assert len(result['stdout'].encode())<=200000 and not result['stderr_truncated'],record
        elif expected=='output_limit':
            assert t['status']=='ERROR' and t['failure_category']=='output_limit' and p.returncode==1,record
            assert t['failed_tool_calls']==1 and result['limit_exceeded'],record
            assert result['stdout_bytes']+result['stderr_bytes']>2000000,record
            assert len(result['stdout'].encode())<=200000 and len(result['stderr'].encode())<=200000,record
        elif expected=='artifact_limit':
            assert t['status']=='ERROR' and t['failure_category']=='artifact_limit' and p.returncode==1,record
            assert not artifact.exists() and not artifact.with_suffix('.tar.partial').exists(),record
            assert t['artifact']['status']=='limit_exceeded' and t['artifact']['bytes_written']<=64000000,record
        elif expected=='exact-limit':
            assert t['status']=='PASS' and result['stdout_bytes']==2000000 and result['output_complete'],record
            assert result['stdout_truncated'] and not result['limit_exceeded'],record
        elif expected=='normal':
            assert t['status']=='PASS' and result['stdout_bytes']==100000 and result['stderr_bytes']==100000,record
            assert not result['stdout_truncated'] and not result['stderr_truncated'],record
    return results[-1]

run('explicit-truncation',"import sys; sys.stdout.write('x'*400001)",'truncated')
run('fast-output',"import os; os.write(1,b'x'*2200000)",'output_limit',3)
run('sustained-output',"import os,time\nfor i in range(100):\n os.write(1,b'x'*100000); time.sleep(.002)",'output_limit')
run('both-streams',"import os,threading\na=threading.Thread(target=lambda: os.write(1,b'x'*1200000)); a.start(); os.write(2,b'e'*1200000); a.join()",'output_limit')
run('oversized-artifact',"from pathlib import Path; Path('large.bin').write_bytes(b'x'*70000000)",'artifact_limit')
run('stderr-limit',"import os; os.write(2,b'e'*2200000)",'output_limit')
run('exact-limit',"import os; os.write(1,b'x'*2000000)",'exact-limit')
run('normal-streams',"import os,threading\na=threading.Thread(target=lambda: os.write(1,b'x'*100000)); a.start(); os.write(2,b'e'*100000); a.join()",'normal')
if not a.observe:
    # Fault injection preserves real cp bytes; it only paces the transport.
    # All other runtime commands exec the real engine without substitution.
    real_engine=shutil.which('podman') or shutil.which('docker')
    shim_dir=a.root/'paced-runtime'; shim_dir.mkdir()
    shim=shim_dir/Path(real_engine).name
    shim.write_text('#!/usr/bin/env python3\n'+"import os,sys,subprocess,time\nREAL="+repr(real_engine)+"\n"
        +"if len(sys.argv)<2 or sys.argv[1]!='cp': os.execv(REAL,[REAL,*sys.argv[1:]])\n"
        +"p=subprocess.Popen([REAL,*sys.argv[1:]],stdout=subprocess.PIPE)\n"
        +"while True:\n b=os.read(p.stdout.fileno(),4096)\n if not b: break\n os.write(1,b); time.sleep(.01)\n"
        +"raise SystemExit(p.wait())\n")
    shim.chmod(0o755)
    paced_env=dict(env,PATH=str(shim_dir)+os.pathsep+env['PATH'])
    code="from pathlib import Path; Path('payload.bin').write_bytes(b'x'*8000000)"
    reference.write_text(json.dumps([{'tool':'shell','arguments':{'command':'python -c '+shlex.quote(code)}},*original]))
    for mode in ('timeout','cancel','sigterm','sigkill-resume'):
        root=a.root/('snapshot-'+mode); root.mkdir()
        cfg=root/'config.json'; cfg.write_text(json.dumps({'tasks':['bugfix-rounding'],'runtime_seconds':5 if mode=='timeout' else 30}))
        with (root/'cli.log').open('w') as log:
            p=subprocess.Popen([str(a.cli),'run','--root',str(root),'--config',str(cfg)],env=paced_env,cwd=copy,stdout=log,stderr=log)
            deadline=time.monotonic()+15; partial=None
            while time.monotonic()<deadline:
                found=list(root.glob('artifacts/*/agent/workspace.tar.partial'))
                if found and found[0].stat().st_size>0: partial=found[0]; break
                if p.poll() is not None: break
                time.sleep(.005)
            assert partial is not None,'Did not reach actual artifact stream'
            rid=json.loads((root/'cli.log').read_text().splitlines()[0])['run_id']
            if mode=='cancel':
                response=cli(['cancel',rid,'--root',str(root)]); assert response.returncode==0,response.stderr
            elif mode=='sigterm': p.send_signal(signal.SIGTERM)
            elif mode=='sigkill-resume': p.kill()
            p.wait(timeout=20)
        if mode=='sigkill-resume':
            assert partial.exists(),'Forced kill should leave evidence for recovery'
            response=cli(['run','--root',str(root),'--resume',rid]); assert response.returncode==1,response.stdout+response.stderr
        db=sqlite3.connect(root/'results.sqlite3')
        trials=[json.loads(row[0]) for row in db.execute('select data from trials order by rowid')]; db.close()
        first=trials[0]; expected={'timeout':'TIMEOUT','cancel':'CANCELLED','sigterm':'INTERRUPTED','sigkill-resume':'INTERRUPTED'}[mode]
        assert first['status']==expected and not first['cleanup_errors'],first
        expected_artifact={'timeout':'timeout','cancel':'cancelled','sigterm':'interrupted','sigkill-resume':'interrupted'}[mode]
        assert first['artifact']['status']==expected_artifact,first
        assert not partial.exists(),first
        assert not partial.with_suffix('').exists(),first
        if mode=='sigkill-resume': assert len(trials)==2 and trials[1]['status']=='PASS',trials
        record={'case':'snapshot-'+mode,'trial_id':first['id'],'status':first['status'],
            'artifact_metadata':first.get('artifact'),'cleanup_errors':first['cleanup_errors'],
            'partial_removed':True,'resumed_status':trials[-1]['status'] if len(trials)>1 else None}
        results.append(record); (a.root/'results.json').write_text(json.dumps(results,indent=2)); print(json.dumps(record),flush=True)
engine=json.loads(cli(['doctor']).stdout)['runtime']
containers=subprocess.check_output([engine,'ps','-a','--format','{{.Names}}'],text=True)
volumes=subprocess.check_output([engine,'volume','ls','--format','{{.Name}}'],text=True)
assert all('abl-'+r['trial_id'] not in containers and 'abl-'+r['trial_id'] not in volumes for r in results)
print('All tested resources removed',flush=True)
