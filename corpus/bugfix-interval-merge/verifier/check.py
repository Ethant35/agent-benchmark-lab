import ast,json,subprocess,sys
from pathlib import Path
W=Path('/workspace')
def run(args):
 p=subprocess.run(args,cwd='/workspace',env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=5,user=65534,group=65534,extra_groups=[])
 assert p.returncode==0,(args,p.stdout,p.stderr)
 return p
try:
    for v,w in [([[1,3],[3,5]],'[[1,5]]'),([[8,9],[1,2],[2,4]],'[[1,4],[8,9]]'),([],'[]'),([[-4,-1],[-2,0]],'[[-4,0]]')]:
        p=run(['python','-c','import subprocess,sys; p=subprocess.run([sys.executable,"app.py"],input=sys.argv[1],text=True,capture_output=True); print(p.stdout,end=""); sys.exit(p.returncode)',json.dumps(v)]); assert p.stdout.strip()==w,p.stdout
    print('PASS: independent task evidence verified')
except Exception as e:
 print('FAIL:',repr(e),file=sys.stderr); raise
