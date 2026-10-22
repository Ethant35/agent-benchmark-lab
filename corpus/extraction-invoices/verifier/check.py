import ast,json,subprocess,sys
from pathlib import Path
W=Path('/workspace')
def run(args):
 p=subprocess.run(args,cwd='/workspace',env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=5,user=65534,group=65534,extra_groups=[])
 assert p.returncode==0,(args,p.stdout,p.stderr)
 return p
try:
    src=json.loads((W/'invoices.json').read_text()); out=json.loads((W/'invoices_out.json').read_text()); assert out==[{'invoice_id':'INV-21','vendor':'Northwind','date':'2026-03-01','amount_cents':1995},{'invoice_id':'INV-22','vendor':'Paper & Co','date':'2026-03-18','amount_cents':7},{'invoice_id':'INV-23','vendor':'Northwind','date':'2026-04-02','amount_cents':12000}]; assert len(out)==len(src) and all(set(x)=={'invoice_id','vendor','date','amount_cents'} for x in out)
    assert all(type(item['amount_cents']) is int for item in out)
    print('PASS: independent task evidence verified')
except Exception as e:
 print('FAIL:',repr(e),file=sys.stderr); raise
