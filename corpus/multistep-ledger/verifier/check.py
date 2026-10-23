import ast,json,subprocess,sys
from pathlib import Path
W=Path('/workspace')
def run(args):
 p=subprocess.run(args,cwd='/workspace',env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=5,user=65534,group=65534,extra_groups=[])
 assert p.returncode==0,(args,p.stdout,p.stderr)
 return p
try:
    for s in ['normalize','total','manifest']: run(['python','pipeline.py',s])
    rows=json.loads((W/'transactions.json').read_text()); totals=json.loads((W/'totals.json').read_text()); m=json.loads((W/'manifest.json').read_text()); assert rows==[{'account':'alpha','cents':125},{'account':'beta','cents':50},{'account':'alpha','cents':200},{'account':'beta','cents':75}]; assert totals==[{'account':'alpha','total_cents':325},{'account':'beta','total_cents':125}]; assert all(set(row)=={'account','total_cents'} and type(row['total_cents']) is int for row in totals); import hashlib; h={p:hashlib.sha256((W/p).read_bytes()).hexdigest() for p in ['transactions.json','totals.json']}; assert m=={'sha256':h,'row_count':4}
    print('PASS: independent task evidence verified')
except Exception as e:
 print('FAIL:',repr(e),file=sys.stderr); raise
