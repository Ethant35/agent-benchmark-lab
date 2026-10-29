import ast,json,subprocess,sys
from pathlib import Path
W=Path('/workspace')
BASELINE = """import json,sys
text=open(sys.argv[1],encoding='utf-8').read()
words=[x.casefold() for x in text.split()]
print(json.dumps({"total":len(words),"counts":{x:words.count(x) for x in sorted(set(words))}},sort_keys=True))
"""
def run(args):
 p=subprocess.run(args,cwd='/workspace',env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=5,user=65534,group=65534,extra_groups=[])
 assert p.returncode==0,(args,p.stdout,p.stderr)
 return p
try:
 names={n.name for n in ast.parse((W/'text_stats.py').read_text()).body if isinstance(n,ast.FunctionDef)}
 assert {'tokenize','count_words'}<=names,names
 cases={'normal.txt':'Red red blue!\n BLUE\tred','empty.txt':'','punctuation.txt':'Hello, hello! ΣIGMA sigma\n','spaces.txt':'  One\tTWO\n'}
 for filename,content in cases.items():
  (W/filename).write_text(content,encoding='utf-8')
  before=run(['python','-c',BASELINE,filename])
  after=run(['python','text_stats.py',filename])
  assert json.loads(after.stdout)==json.loads(before.stdout),(filename,before.stdout,after.stdout)
 assert json.loads(run(['python','text_stats.py','normal.txt']).stdout)=={'total':5,'counts':{'blue':1,'blue!':1,'red':3}}
 print('PASS: refactored behavior matches trusted baseline for normal, empty, punctuation and whitespace cases')
except Exception as e:
 print('FAIL:',repr(e),file=sys.stderr); raise
