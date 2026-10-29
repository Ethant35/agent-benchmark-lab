from support import *
import csv,io,hashlib
from decimal import Decimal

def validate(text):
    source=list(csv.DictReader(io.StringIO(text)))
    rows=[{'account':r['account'].lower(),'cents':int(Decimal(r['amount'])*100)} for r in source]
    totals={}
    for row in rows: totals[row['account']]=totals.get(row['account'],0)+row['cents']
    equal(read('transactions.json'),rows)
    equal(read('totals.json'),[{'account':a,'total_cents':n} for a,n in totals.items()])
    equal(read('manifest.json'),{'sha256':{p:hashlib.sha256((W/p).read_bytes()).hexdigest() for p in ['transactions.json','totals.json']},'row_count':len(rows)})
validate('account,amount\nALPHA,1.25\nbeta,0.50\nalpha,2.00\nBETA,0.75\n')
for text in ['account,amount\nZETA,-1.23\na,0.07\nzeta,0.00\nA,2.00\n','account,amount\n']:
    (W/'transactions.csv').write_text(text)
    for output in ['transactions.json','totals.json','manifest.json']: (W/output).unlink(missing_ok=True)
    for step in ['normalize','total','manifest']: run(['python','pipeline.py',step])
    validate(text)

print('PASS: version 2.0 contract verified')
