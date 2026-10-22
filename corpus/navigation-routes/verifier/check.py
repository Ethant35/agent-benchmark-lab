import ast,json,hashlib,subprocess,sys
from pathlib import Path
W=Path('/workspace')
try:
    src=(W/'routes.py').read_bytes(); assert hashlib.sha256(src).hexdigest()=='7afbbd123bb2745f6c12f930a7d65889bac3fb9fbffef589a6820248598c3e24'
    routes=ast.literal_eval(src.decode().split('=',1)[1].strip()); d=json.loads((W/'routes.json').read_text()); explanation=d.pop('explanation'); assert d=={'route_count': 4, 'methods_by_path': {'/health': ['GET'], '/items': ['GET', 'POST'], '/items/{item_id}': ['DELETE']}, 'health_path': '/health', 'source': 'routes.py'},d
    assert type(d['route_count']) is int
    assert d['source']=='routes.py' and all(x.casefold() in explanation.casefold() for x in ['/health','/items','GET','POST','DELETE']) and len(explanation.casefold().strip())>=40
    print('PASS: source attribution, unchanged-source digest, and extracted facts verified')
except Exception as e:
    print('FAIL:',repr(e),file=sys.stderr); raise
