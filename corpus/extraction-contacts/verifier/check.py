import ast,json,subprocess,sys
from pathlib import Path
W=Path('/workspace')
def run(args):
 p=subprocess.run(args,cwd='/workspace',env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=5,user=65534,group=65534,extra_groups=[])
 assert p.returncode==0,(args,p.stdout,p.stderr)
 return p
try:
    out=json.loads((W/'contacts.json').read_text()); assert out==[{'name':'Maya Chen','email':'maya.chen@example.org','phone':'+1 (541) 555-0198'},{'name':'Omar Ali','email':'omar.ali@example.net','phone':'503-555-0101'},{'name':'Rina Patel','email':'rina.p@example.com','phone':'extension 44'}]; assert all(set(x)=={'name','email','phone'} for x in out)
    print('PASS: independent task evidence verified')
except Exception as e:
 print('FAIL:',repr(e),file=sys.stderr); raise
