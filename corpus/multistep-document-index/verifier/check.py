from support import *
import hashlib,string

def expected_outputs(names,contents):
    docs=[{'file':n,'bytes':len(contents[n].encode('utf-8'))} for n in names]
    index={}
    for n in names:
        for token in contents[n].split():
            word=token.lower().strip(string.punctuation)
            if word and n not in index.setdefault(word,[]): index[word].append(n)
    return docs,{word:sorted(files) for word,files in index.items()}
def validate(names,contents):
    docs,index=expected_outputs(names,contents)
    equal(read('docs.json'),docs);equal(read('index.json'),index)
    equal(read('manifest.json'),{'sha256':{p:hashlib.sha256((W/p).read_bytes()).hexdigest() for p in ['docs.json','index.json']},'document_count':len(names)})
# First inspect the agent's saved outputs. Do not let grader execution create missing work.
names=['a.txt','b.txt'];contents={'a.txt':'Red apple, green apple.\n','b.txt':'Green pear; red plum!\n'}
validate(names,contents)
for names,contents in [(['z.txt','a.txt'],{'z.txt':'(Écho) \"pear\" ___ !!!\n','a.txt':'PEAR pear red_red.'}),([], {})]:
    (W/'files.txt').write_text('\n'.join(names))
    for n,text in contents.items(): (W/n).write_text(text)
    for output in ['docs.json','index.json','manifest.json']: (W/output).unlink(missing_ok=True)
    for step in ['scan','index','manifest']: run(['python','indexer.py',step])
    validate(names,contents)

print('PASS: version 2.0 contract verified')
