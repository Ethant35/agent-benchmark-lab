from support import *
expected=[{'name':'Maya Chen','email':'maya.chen@example.org','phone':'+1 (541) 555-0198'},{'name':'Omar Ali','email':'omar.ali@example.net','phone':'503-555-0101'},{'name':'Rina Patel','email':'rina.p@example.com','phone':'extension 44'}]
equal(read('contacts.json'),expected)

print('PASS: version 2.0 contract verified')
