"""Local synthetic history measurement, not model performance or a live score.

Run: python tests/history_performance.py --root .abl/history-measurement
Uses the pre-readiness Store from Git for an equivalent baseline on the same DB.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
import tracemalloc
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from abl.store import Store, aggregate


def measure(operation):
    gc.collect()
    tracemalloc.start()
    start = time.perf_counter()
    result = operation()
    encoded = json.dumps(result, separators=(',', ':')).encode()
    elapsed = time.perf_counter() - start
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return dict(seconds=elapsed, peak_python_bytes=peak, response_bytes=len(encoded)), result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--baseline', default='381caf2')
    args = parser.parse_args()
    if args.root.exists():
        raise SystemExit('Use a new measurement directory; existing evidence is preserved.')
    store = Store(args.root)
    with store.connect() as db:
        for index in range(10000):
            trial = dict(id=f'{index:032x}', run_id=f'{index // 1000:032x}', slot=index,
                         runner='agent', provider='controlled', model='synthetic',
                         config_hash='configuration', task_id='task-'+str(index % 12),
                         task_version='1', category='test', status='PASS' if index % 3 else 'FAIL',
                         wall_seconds=2, ttft_seconds=.1, input_tokens=100, output_tokens=10,
                         cached_input_tokens=50, cost_usd=.01, cost_source='provider.usage.cost',
                         tool_calls=2, failed_tool_calls=0,
                         verifier={'stdout':'x'*8192}, provider_requests=[{'raw':'x'*4096}])
            db.execute('INSERT INTO trials VALUES(?,?,?,?)',
                       (trial['id'],trial['run_id'],index,json.dumps(trial)))
        plan = [list(r) for r in db.execute('EXPLAIN QUERY PLAN SELECT data FROM trials WHERE run_id=?', ('0'*32,))]
    source = subprocess.check_output(['git','show',args.baseline+':abl/store.py'])
    baseline_module = types.ModuleType('baseline_store')
    exec(compile(source, '<trusted repository baseline>', 'exec'), baseline_module.__dict__)
    old = baseline_module.Store(args.root)
    observations = {'baseline':[], 'compact':[]}
    for iteration in range(3):
        # Alternate order to reduce warm-cache/order bias. Both touch the same data.
        for variant in (['baseline','compact'] if iteration % 2 == 0 else ['compact','baseline']):
            if variant == 'baseline':
                operation = lambda: dict(items=old.trials(), summary=baseline_module.aggregate(old.trials()))
            else:
                operation = lambda: dict(page=store.trial_page(), overview=store.overview())
            observation, result = measure(operation)
            observations[variant].append(observation)
            if variant == 'baseline':
                baseline_summary = result['summary']
            else:
                current_summary = result['overview']['summary']
                assert result['page']['total'] == 10000
                assert result['overview']['chart_total'] == 10000
                assert result['overview']['chart_sampled']
    for key, value in baseline_summary.items():
        if key not in ('categories','groups'):
            assert current_summary[key] == value, (key,current_summary[key],value)
    report = dict(author='Ethan',kind='controlled synthetic persisted history',
                  python=platform.python_version(),trials=10000,
                  evidence_bytes_per_trial=12288,baseline_ref=args.baseline,
                  baseline_store_sha256=hashlib.sha256(source).hexdigest(),
                  current_store_sha256=hashlib.sha256(Path('abl/store.py').read_bytes()).hexdigest(),
                  observations=observations,
                  medians={name:{key:statistics.median(r[key] for r in rows)
                                 for key in rows[0]} for name,rows in observations.items()},
                  run_filter_query_plan=plan,
                  limits='Python allocations only; includes JSON encoding; local warm OS cache; not field-user telemetry.')
    (args.root/'measurement.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
