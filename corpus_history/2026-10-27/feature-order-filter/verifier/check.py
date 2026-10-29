import ast,json,subprocess,sys
from pathlib import Path
W=Path('/workspace')
def run(args):
 p=subprocess.run(args,cwd='/workspace',env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=5,user=65534,group=65534,extra_groups=[])
 assert p.returncode==0,(args,p.stdout,p.stderr)
 return p
try:
    p=run(['python','filter_orders.py','--status','paid','--minimum','20']); assert json.loads(p.stdout)==[{'id':'a','status':'paid','total':20},{'id':'d','status':'paid','total':45}]
    p=run(['python','filter_orders.py','--status','pending','--minimum','81']); assert json.loads(p.stdout)==[]
    print('PASS: independent task evidence verified')
except Exception as e:
 print('FAIL:',repr(e),file=sys.stderr); raise
