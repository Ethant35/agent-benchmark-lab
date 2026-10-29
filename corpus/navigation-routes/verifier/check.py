from support import *
import hashlib
assert hashlib.sha256((W/'routes.py').read_bytes()).hexdigest()=='7afbbd123bb2745f6c12f930a7d65889bac3fb9fbffef589a6820248598c3e24', 'source changed'
equal(read('routes.json'),{'route_count': 4, 'methods_by_path': {'/health': ['GET'], '/items': ['GET', 'POST'], '/items/{item_id}': ['DELETE']}, 'health_path': '/health', 'source': 'routes.py', 'explanation': {'health': {'path': '/health', 'methods': ['GET']}, 'collection': {'path': '/items', 'methods': ['GET', 'POST']}, 'item': {'path': '/items/{item_id}', 'methods': ['DELETE']}}})

print('PASS: version 2.0 contract verified')
