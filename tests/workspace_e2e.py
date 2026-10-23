"""Actual container workspace quota via the public CLI. Author: Ethan."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import sqlite3
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--cli',type=Path,required=True)
args=parser.parse_args()
root=args.root.resolve(); source=Path(__file__).resolve().parents[1]
if root.exists(): raise SystemExit('Use a fresh evidence root')
copy=root/'source'
shutil.copytree(source/'abl',copy/'abl',ignore=shutil.ignore_patterns('__pycache__','static'))
shutil.copytree(source/'corpus',copy/'corpus',ignore=shutil.ignore_patterns('__pycache__'))
reference=copy/'corpus/bugfix-rounding/reference.json'
original=json.loads(reference.read_text())
probe='''import errno,json,os,pathlib
stats=os.statvfs('/workspace')
bounded=False
try:
 with open('/workspace/fill','wb') as f:
  for _ in range(130): f.write(b'x'*1048576)
except OSError as e:
 if e.errno != errno.ENOSPC: raise
 bounded=True
pathlib.Path('/workspace/fill').unlink()
print(json.dumps({'quota_probe':True,'bytes':stats.f_blocks*stats.f_frsize,'inodes':stats.f_files,'enospc':bounded}))
'''
reference.write_text(json.dumps([{'tool':'shell','arguments':{'command':'python -c '+shlex.quote(probe)}},*original]))
data=root/'data'
result=subprocess.run([str(args.cli.resolve()),'run','--root',str(data),'--task','bugfix-rounding'],
                      cwd=copy,env=dict(os.environ,PYTHONPATH=str(copy)),capture_output=True,text=True,timeout=120)
(root/'cli.log').write_text(result.stdout+result.stderr)
with sqlite3.connect(data/'results.sqlite3') as db:
    trial=json.loads(db.execute('SELECT data FROM trials').fetchone()[0])
events=[json.loads(line) for line in Path(trial['artifact_dir'],'trace.jsonl').read_text().splitlines()]
tool=next(e for e in events if e['kind']=='tool')
probe_result=json.loads(tool['result']['stdout'].strip())
evidence=dict(author='Ethan',kind='real container workspace limit',probe=probe_result,
              status=trial['status'],cleanup_errors=trial['cleanup_errors'],artifact=trial.get('artifact'))
(root/'result.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps(evidence,indent=2))
assert probe_result['bytes']==128*1024*1024 and probe_result['inodes']==16384 and probe_result['enospc']
assert trial['status']=='PASS' and result.returncode==0
assert not trial['cleanup_errors']
