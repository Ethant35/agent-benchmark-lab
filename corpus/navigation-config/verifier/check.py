from support import *
import hashlib
assert hashlib.sha256((W/'settings.py').read_bytes()).hexdigest()=='fbce7e223f91664aa6558ba6926b439b1308adf9561d01ad03d9a31742b0c560', 'source changed'
equal(read('answer.json'),{'default_port': 8123, 'retry_limit': 4, 'cache_enabled': False, 'supported_formats': ['json', 'csv', 'ndjson'], 'source': 'settings.py', 'explanation': {'listener': {'symbol': 'DEFAULT_PORT', 'value': 8123}, 'retry': {'symbol': 'RETRY_LIMIT', 'value': 4}, 'cache': {'symbol': 'CACHE_ENABLED', 'value': False}, 'formats': {'symbol': 'SUPPORTED_FORMATS', 'value': ['json', 'csv', 'ndjson']}}})

print('PASS: version 2.0 contract verified')
