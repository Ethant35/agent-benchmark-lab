import ast,json,hashlib,subprocess,sys
from pathlib import Path
W=Path('/workspace')
try:
    src=(W/'settings.py').read_bytes(); assert hashlib.sha256(src).hexdigest()=='fbce7e223f91664aa6558ba6926b439b1308adf9561d01ad03d9a31742b0c560'
    d=json.loads((W/'answer.json').read_text()); explanation=d.pop('explanation'); assert d=={'default_port': 8123, 'retry_limit': 4, 'cache_enabled': False, 'supported_formats': ['json', 'csv', 'ndjson'], 'source': 'settings.py'},d
    assert type(d['default_port']) is int and type(d['retry_limit']) is int and type(d['cache_enabled']) is bool
    assert d['source']=='settings.py' and all(x in explanation.casefold() for x in ['port','retry','caching','formats']) and len(explanation.casefold().strip())>=40
    print('PASS: source attribution, unchanged-source digest, and extracted facts verified')
except Exception as e:
    print('FAIL:',repr(e),file=sys.stderr); raise
