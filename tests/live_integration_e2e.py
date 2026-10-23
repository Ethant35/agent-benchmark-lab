"""Opt-in live protocol acceptance with a separately versioned latency allowance.
Author: Ethan. This is not a bundled-corpus benchmark score. No automatic retries.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import yaml

p=argparse.ArgumentParser()
p.add_argument('--python',type=Path,required=True,help='Python from the installed wheel environment')
p.add_argument('--cli',type=Path,required=True)
p.add_argument('--config-a',type=Path,required=True)
p.add_argument('--config-b',type=Path,required=True)
p.add_argument('--root',type=Path,required=True)
a=p.parse_args()
a.root=a.root.resolve();a.python=a.python.absolute();a.cli=a.cli.absolute()
if a.root.exists():raise SystemExit('Use a fresh integration root')
for path in [a.config_a,a.config_b]:
 c=yaml.safe_load(path.read_text())
 assert c['spend_limit_usd']<=.02 and c['max_requests']<=8 and c['max_output_tokens']<=2048
 assert c.get('runtime_seconds')==120 and c.get('tasks')==['bugfix-rounding']
assert yaml.safe_load(a.config_a.read_text())['streaming'] is True
assert yaml.safe_load(a.config_b.read_text())['streaming'] is False
source=Path(subprocess.check_output([str(a.python),'-I','-c','import abl; print(abl.__path__[0])'],text=True).strip())
assert (source/'corpus/bugfix-rounding/task.yaml').is_file(),'Use an installed wheel, not editable source'
a.root.mkdir(parents=True,mode=0o700)
copy=a.root/'package-copy';shutil.copytree(source,copy/'abl',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
def inventory(folder):
 return {str(f.relative_to(folder)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(folder.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
before=inventory(source)
task_path=copy/'abl/corpus/bugfix-rounding/task.yaml'
original=yaml.safe_load(task_path.read_text());assert original['runtime_seconds']==30
revised=dict(original,runtime_seconds=120,version=original['version']+'-integration-120s')
task_path.write_text(yaml.safe_dump(revised,sort_keys=False))
after=inventory(copy/'abl')
changed=[name for name in before if before[name]!=after.get(name)]
assert changed==['corpus/bugfix-rounding/task.yaml']
assert {k:v for k,v in original.items() if k not in ('version','runtime_seconds')}=={k:v for k,v in revised.items() if k not in ('version','runtime_seconds')}
manifest={'author':'Ethan','purpose':'live integration, not benchmark performance','changed_files':changed,'original_task':original,'integration_task':revised,'original_package_sha256':before,'integration_package_sha256':after,'local_reserve_total_usd':.06}
(a.root/'integration-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
env=dict(os.environ,PYTHONPATH=str(copy))
result=subprocess.run([str(a.python),str(Path(__file__).with_name('live_e2e.py').resolve()),'--config-a',str(a.config_a.resolve()),'--config-b',str(a.config_b.resolve()),'--root',str(a.root/'results'),'--cli',str(a.cli)],env=env,timeout=450)
assert inventory(source)==before,'Installed package must remain unchanged'
raise SystemExit(result.returncode)
