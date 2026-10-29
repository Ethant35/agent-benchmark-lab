from support import *
from decimal import Decimal, ROUND_HALF_UP
cases=['1.005','2.675','-1.005','0','9.999','-0.005','-0.004','123456.995','1e-3']
cases += [str(Decimal(n)/1000) for n in range(-9525,9526,635)]
for value in cases:
    expected=str(Decimal(value).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
    equal(call('app.py','format_price',[value]),expected)
    assert run(['python','app.py',value]).stdout.strip()==expected

print('PASS: version 2.0 contract verified')
