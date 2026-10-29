from support import *
import csv,io
cases=['sku,quantity,unit_price\na,2,3.50\na,1,1.25\nb,-1,8.00\n','sku,quantity,unit_price\n','sku,quantity,unit_price\nx,-2,1.25\nx,3,0.10\ny,1,0.105\n','sku,quantity,unit_price\nz,0,8.88\n','sku,quantity,unit_price\nz,1,1.005\na,-1,2.675\nz,2,0.07\n']
for i,text in enumerate(cases):
    rows=list(csv.DictReader(io.StringIO(text)));expected={}
    for row in rows:
        k=row['sku'];expected[k]=round(expected.get(k,0)+int(row['quantity'])*float(row['unit_price']),2)
    filename=f'case-{i}.csv';(W/filename).write_text(text)
    equal(call('summary.py','parse_rows',[filename]),rows)
    assert call('summary.py','summarize',[rows])==expected
    assert sorted_json(cli_using('summary.py',[filename],['parse_rows','summarize']))==expected

print('PASS: version 2.0 contract verified')
