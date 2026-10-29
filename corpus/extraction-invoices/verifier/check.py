from support import *
expected=[{'invoice_id':'INV-21','vendor':'Northwind','date':'2026-03-01','amount_cents':1995},{'invoice_id':'INV-22','vendor':'Paper & Co','date':'2026-03-18','amount_cents':7},{'invoice_id':'INV-23','vendor':'Northwind','date':'2026-04-02','amount_cents':12000}]
equal(read('invoices_out.json'),expected)

print('PASS: version 2.0 contract verified')
