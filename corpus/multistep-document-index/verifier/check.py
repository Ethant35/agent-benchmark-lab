import ast,json,subprocess,sys
from pathlib import Path
W=Path('/workspace')
def run(args):
 p=subprocess.run(args,cwd='/workspace',env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=5,user=65534,group=65534,extra_groups=[])
 assert p.returncode==0,(args,p.stdout,p.stderr)
 return p
try:
    for s in ['scan','index','manifest']: run(['python','indexer.py',s])
    docs=json.loads((W/'docs.json').read_text()); idx=json.loads((W/'index.json').read_text()); m=json.loads((W/'manifest.json').read_text()); assert docs==[{'file':'a.txt','bytes':24},{'file':'b.txt','bytes':22}]; assert idx=={'apple':['a.txt'],'green':['a.txt','b.txt'],'pear':['b.txt'],'plum':['b.txt'],'red':['a.txt','b.txt']}; import hashlib; h={p:hashlib.sha256((W/p).read_bytes()).hexdigest() for p in ['docs.json','index.json']}; assert m=={'sha256':h,'document_count':2}
    print('PASS: independent task evidence verified')
except Exception as e:
 print('FAIL:',repr(e),file=sys.stderr); raise
