from support import *
import re,unicodedata
cases=['Crème Brûlée — Café & Tea',' A__B!! ','123','!!!','','Ångström déjà-vu','Straße Łódź','東京','a\tb  c','---ÉÉ---','ﬁ ligature','Cafe\u0301',"rock'n'roll"]
for text in cases:
    ascii_text=unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower()
    expected='-'.join(re.findall('[a-z0-9]+',ascii_text))
    equal(call('slugify.py','slugify',[text]),expected)
    assert run(['python','slugify.py'],text+'\n').stdout.strip()==expected

print('PASS: version 2.0 contract verified')
