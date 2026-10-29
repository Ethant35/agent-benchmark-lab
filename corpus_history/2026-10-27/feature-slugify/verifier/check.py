import ast,json,subprocess,sys
from pathlib import Path
W=Path('/workspace')
def run(args, input=None):
 p=subprocess.run(args,cwd='/workspace',env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=5,user=65534,group=65534,extra_groups=[],input=input)
 assert p.returncode==0,(args,p.stdout,p.stderr)
 return p
try:
    for x,y in [('Crème Brûlée — Café & Tea','creme-brulee-cafe-tea'),(' A__B!! ','a-b'),('123','123'),('!!!','')]:
        p=run(['python','slugify.py'],x+'\n'); assert p.stdout.strip()==y,(x,p.stdout)
    print('PASS: independent task evidence verified')
except Exception as e:
 print('FAIL:',repr(e),file=sys.stderr); raise
