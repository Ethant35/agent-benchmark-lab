"""Trusted verifier helpers. Candidate imports and calls run only as UID 65534."""
import json, subprocess
from pathlib import Path
W=Path('/workspace')
def run(args, input=None):
    p=subprocess.run(args,cwd=W,env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=5,user=65534,group=65534,extra_groups=[],input=input)
    assert p.returncode==0,(args,p.stdout,p.stderr)
    return p

def unique(pairs):
    result={}
    for k,v in pairs:
        assert k not in result, ('duplicate JSON key',k)
        result[k]=v
    return result

def load(text): return json.loads(text,object_pairs_hook=unique)
def read(name): return load((W/name).read_text())
def equal(actual,expected):
    assert type(actual) is type(expected), ('type',type(actual).__name__,type(expected).__name__)
    if isinstance(expected,dict):
        assert set(actual)==set(expected),('keys',actual,expected)
        for k in expected: equal(actual[k],expected[k])
    elif isinstance(expected,list):
        assert len(actual)==len(expected),('length',actual,expected)
        for a,e in zip(actual,expected): equal(a,e)
    else: assert actual==expected,(actual,expected)

def call(filename,function,args):
    code="import json,runpy,sys\nm=runpy.run_path(sys.argv[1]); result=m[sys.argv[2]](*json.loads(sys.argv[3]))\ndef check(value):\n    assert type(value) in (dict,list,str,int,float,bool,type(None)), ('unsupported return type',type(value).__name__)\n    if isinstance(value,dict):\n        assert all(type(k) is str for k in value), 'return object keys must be strings'\n        for child in value.values():check(child)\n    elif isinstance(value,list):\n        for child in value:check(child)\ncheck(result)\nprint(json.dumps(result))\n"
    return load(run(['python','-c',code,filename,function,json.dumps(args)]).stdout)

def cli_using(filename,args,names):
    code="import runpy,sys\nfilename=sys.argv[1]; required=set(sys.argv[2].split(',')); sys.argv=[filename]+sys.argv[3:]; seen=set()\ndef profile(frame,event,arg):\n    if event=='call' and frame.f_code.co_filename.endswith('/'+filename): seen.add(frame.f_code.co_name)\nsys.setprofile(profile)\nrunpy.run_path('/workspace/'+filename,run_name='__main__')\nsys.setprofile(None)\nassert required<=seen, ('CLI did not call helpers',required-seen)\n"
    return run(['python','-c',code,filename,','.join(names),*args]).stdout

def sorted_json(text):
    def pairs(items):
        assert [k for k,v in items]==sorted(k for k,v in items), 'JSON keys must be sorted'
        return unique(items)
    return json.loads(text,object_pairs_hook=pairs)
