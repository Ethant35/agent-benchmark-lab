import ast,json,subprocess,sys
from pathlib import Path
W=Path('/workspace')
BASELINE = """import csv,json,sys
rows=list(csv.DictReader(open(sys.argv[1],newline='',encoding='utf-8')))
out={}
for r in rows:
 k=r['sku']; out[k]=round(out.get(k,0)+int(r['quantity'])*float(r['unit_price']),2)
print(json.dumps(out,sort_keys=True))
"""
def run(args):
 p=subprocess.run(args,cwd='/workspace',env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=5,user=65534,group=65534,extra_groups=[])
 assert p.returncode==0,(args,p.stdout,p.stderr)
 return p
try:
 names={n.name for n in ast.parse((W/'summary.py').read_text()).body if isinstance(n,ast.FunctionDef)}
 assert {'parse_rows','summarize'}<=names,names
 cases={
  'normal.csv':'sku,quantity,unit_price\na,2,3.50\na,1,1.25\nb,-1,8.00\n',
  'empty.csv':'sku,quantity,unit_price\n',
  'negative-decimal.csv':'sku,quantity,unit_price\nx,-2,1.25\nx,3,0.10\ny,1,0.105\n',
  'zero.csv':'sku,quantity,unit_price\nz,0,8.88\n'
 }
 for filename,content in cases.items():
  (W/filename).write_text(content,encoding='utf-8')
  before=run(['python','-c',BASELINE,filename])
  after=run(['python','summary.py',filename])
  assert json.loads(after.stdout)==json.loads(before.stdout),(filename,before.stdout,after.stdout)
 print('PASS: refactored behavior matches trusted baseline for normal, empty, negative and decimal CSV cases')
except Exception as e:
 print('FAIL:',repr(e),file=sys.stderr); raise
