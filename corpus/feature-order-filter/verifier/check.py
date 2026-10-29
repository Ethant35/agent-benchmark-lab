from support import *
datasets=[read('orders.json'),[{'id':'x','status':'pending','total':20.5},{'id':'y','status':'paid','total':-2},{'id':'z','status':'pending','total':20.49},{'id':'w','status':'paid','total':20.5,'note':'keep me'}],[]]
for orders in datasets:
    (W/'orders.json').write_text(json.dumps(orders))
    for status,minimum in [('paid','20'),('pending','81'),('pending','20.5'),('paid','-2'),('absent','0'),('paid','20.5')]:
        expected=[r for r in orders if r['status']==status and r['total']>=float(minimum)]
        equal(load(run(['python','filter_orders.py','--status',status,'--minimum',minimum]).stdout),expected)

print('PASS: version 2.0 contract verified')
