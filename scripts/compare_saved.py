"""Export a matched comparison from an existing database opened read-only.

Author: Ethan
Run from the repository with: uv run --frozen python -m scripts.compare_saved ...
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

from abl.comparison import matched_comparison
from abl.store import COMPACT_SELECT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--left', required=True)
    parser.add_argument('--right', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == args.database.resolve() or args.output.is_symlink():
        parser.error('Output must be a separate regular report file')
    db = sqlite3.connect(args.database.resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute('BEGIN')
        fields = ('task_artifact_id', 'fixture_hash', 'image_id')
        extra = ','.join(f"json_extract(data, '$.{field}') AS {field}" for field in fields)
        rows = [dict(r) for r in db.execute('SELECT '+COMPACT_SELECT+','+extra+
                ",json_extract(data, '$.verifier.exit_code') AS verifier_exit_code FROM trials ORDER BY rowid")]
        runs = {r['id']: {**dict(r), 'config': json.loads(r['config'])} for r in db.execute('SELECT * FROM runs')}
        manifests = {r['run_id']: json.loads(r['data']) for r in db.execute('SELECT * FROM run_manifests')}
    finally:
        db.close()
    result = matched_comparison(rows, runs, manifests, args.left, args.right)
    result['author'] = 'Ethan'
    result['source_database'] = str(args.database)
    result['input_snapshot_sha256'] = hashlib.sha256(json.dumps(
        {'rows': rows, 'runs': runs, 'manifests': manifests}, sort_keys=True).encode()).hexdigest()
    result['new_provider_calls'] = 0
    result['new_provider_cost_usd'] = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"{result['matched_tasks']} matched task contracts -> {args.output}")


if __name__ == '__main__':
    main()
