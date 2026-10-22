import ast,json,subprocess,sys
from pathlib import Path
W=Path('/workspace')
def run(args):
 p=subprocess.run(args,cwd='/workspace',env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=5,user=65534,group=65534,extra_groups=[])
 assert p.returncode==0,(args,p.stdout,p.stderr)
 return p
try:
    for x,y in [('1.005','1.01'),('2.675','2.68'),('-1.005','-1.01'),('0','0.00'),('9.999','10.00')]:
        p=run(['python','app.py',x]); assert p.stdout.strip()==y,(x,p.stdout,p.stderr)
    print('PASS: independent task evidence verified')
except Exception as e:
 print('FAIL:',repr(e),file=sys.stderr); raise
