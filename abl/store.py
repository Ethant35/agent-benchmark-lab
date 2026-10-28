"""SQLite persistence, atomic state transitions, and denominator-aware reports."""
import csv
import io
import json
import math
import os
import sqlite3
import statistics
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat()

# List endpoints expose measurements, never response bodies or execution evidence.
COMPACT_FIELDS = (
    'id', 'run_id', 'slot', 'task_id', 'task_version', 'category', 'runner',
    'provider', 'model', 'config_hash', 'status', 'failure_category',
    'started_at', 'completed_at', 'wall_seconds', 'ttft_seconds', 'api_seconds',
    'input_tokens', 'output_tokens', 'cached_input_tokens', 'tool_calls',
    'failed_tool_calls', 'retry_count', 'timed_out', 'cost_usd', 'cost_source',
    'known_cost_subtotal_usd', 'corpus_hash',
)
COMPACT_SELECT = ','.join(f"json_extract(data, '$.{key}') AS {key}" for key in COMPACT_FIELDS)
FILTER_COLUMNS = {'id': 'id', 'run_id': 'run_id'} | {
    key: f"json_extract(data, '$.{key}')" for key in
    ('provider', 'model', 'task_id', 'status', 'runner', 'config_hash')
}


def where_clause(filters):
    clauses, values = [], []
    for key, value in filters.items():
        if key not in FILTER_COLUMNS:
            raise ValueError(f'Unknown trial filter: {key}')
        if value:
            clauses.append(FILTER_COLUMNS[key] + '=?')
            values.append(value)
    return (' WHERE ' + ' AND '.join(clauses) if clauses else ''), values


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Existing v1 stores used the caller's umask. Restrict traversal too,
        # so historical artifact files become private without rewriting evidence.
        self.root.chmod(0o700)
        path=self.root/'results.sqlite3'
        if path.is_symlink(): raise ValueError('Result database must not be a symlink')
        descriptor=os.open(path,os.O_CREAT|os.O_WRONLY|os.O_NOFOLLOW,0o600)
        os.close(descriptor)
        path.chmod(0o600)
        with self.connect() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, status TEXT, created_at TEXT, config TEXT, cancel INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS trials(id TEXT PRIMARY KEY, run_id TEXT NOT NULL, slot INTEGER NOT NULL, data TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS trials_run ON trials(run_id);
            CREATE TABLE IF NOT EXISTS run_manifests(run_id TEXT PRIMARY KEY, data TEXT NOT NULL);
            ''')
    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.root/'results.sqlite3', timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        except sqlite3.DatabaseError as error:
            raise ValueError('Result store unavailable or corrupt; stop writers and restore a verified backup. '+str(error)) from error
        finally:
            db.close()
    def create_run(self, rid, config, manifest=None):
        with self.connect() as db:
            db.execute('INSERT INTO runs VALUES(?,?,?,?,0)', (rid,'RUNNING',now(),json.dumps(config)))
            if manifest is not None:
                db.execute('INSERT INTO run_manifests VALUES(?,?)', (rid,json.dumps(manifest,sort_keys=True)))
    def manifest(self, rid):
        with self.connect() as db:
            row = db.execute('SELECT data FROM run_manifests WHERE run_id=?', (rid,)).fetchone()
            return json.loads(row[0]) if row else None
    def runs(self):
        with self.connect() as db:
            return [{**dict(r), 'config':json.loads(r['config'])} for r in db.execute('SELECT * FROM runs ORDER BY created_at DESC')]
    def run(self, rid):
        with self.connect() as db:
            row = db.execute('SELECT * FROM runs WHERE id=?', (rid,)).fetchone()
            return {**dict(row), 'config':json.loads(row['config'])} if row else None
    def state(self, rid, status, cancel=None):
        with self.connect() as db:
            db.execute('UPDATE runs SET status=? WHERE id=?',(status,rid))
            if cancel is not None:
                db.execute('UPDATE runs SET cancel=? WHERE id=?',(int(cancel),rid))
    def cancelled(self, rid):
        with self.connect() as db:
            row = db.execute('SELECT cancel FROM runs WHERE id=?',(rid,)).fetchone()
            return bool(row and row[0])
    def save(self, trial):
        with self.connect() as db:
            db.execute('INSERT INTO trials VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data',
                (trial['id'],trial['run_id'],trial['slot'],json.dumps(trial)))
    def trials(self, **filters):
        where, values = where_clause(filters)
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT data FROM trials'+where+' ORDER BY rowid', values)]

    def trial_page(self, limit=100, offset=0, **filters):
        if not 1 <= limit <= 200 or offset < 0:
            raise ValueError('Page limit must be 1..200 and offset must be nonnegative')
        where, values = where_clause(filters)
        with self.connect() as db:
            # One read snapshot keeps count and page consistent during a run.
            db.execute('BEGIN')
            total = db.execute('SELECT count(*) FROM trials'+where, values).fetchone()[0]
            items = [dict(r) for r in db.execute(
                'SELECT '+COMPACT_SELECT+' FROM trials'+where+' ORDER BY rowid DESC LIMIT ? OFFSET ?',
                [*values, limit, offset])]
        return dict(items=items, total=total, limit=limit, offset=offset)

    def schedule_snapshot(self, run_id=None, provider=None, model=None, task_id=None, *, db=None):
        """Read candidate run, manifest and attempts from one SQLite snapshot."""
        if db is None:
            with self.connect() as connection:
                connection.execute('BEGIN')
                return self._schedule_snapshot(connection, run_id, provider, model, task_id)
        return self._schedule_snapshot(db, run_id, provider, model, task_id)

    def _schedule_snapshot(self, db, run_id=None, provider=None, model=None, task_id=None):
        runs = [dict(row) for row in db.execute('SELECT * FROM runs ORDER BY created_at DESC')]
        for run in runs:
            if run_id and run['id'] != run_id:
                continue
            config = json.loads(run['config'])
            if provider and config.get('provider') != provider:
                continue
            if model and config.get('model') != model:
                continue
            manifest_row = db.execute('SELECT data FROM run_manifests WHERE run_id=?',
                                      (run['id'],)).fetchone()
            manifest = json.loads(manifest_row[0]) if manifest_row else None
            tasks = manifest.get('tasks', []) if isinstance(manifest, dict) else []
            if task_id and task_id not in {entry.get('id') for entry in tasks if isinstance(entry, dict)}:
                continue
            run['config'] = config
            attempts = [dict(row) for row in db.execute(
                'SELECT '+COMPACT_SELECT+' FROM trials WHERE run_id=? ORDER BY rowid', (run['id'],))]
            return run, manifest, attempts
        return None, None, []

    def overview(self, **filters):
        where, values = where_clause(filters)
        with self.connect() as db:
            db.execute('BEGIN')
            rows = [dict(r) for r in db.execute(
                'SELECT '+COMPACT_SELECT+' FROM trials'+where+' ORDER BY rowid DESC', values)]
            # Scan history once for all facets; avoid three passes over evidence JSON.
            facet_rows = db.execute("SELECT DISTINCT json_extract(data, '$.provider'), json_extract(data, '$.model'), json_extract(data, '$.task_id') FROM trials").fetchall()
            facets = {label: sorted({r[index] for r in facet_rows if r[index]})
                      for index, label in enumerate(('providers','models','tasks'))}
            schedule_snapshot = self.schedule_snapshot(
                filters.get('run_id'), filters.get('provider'), filters.get('model'),
                filters.get('task_id'), db=db)
        from .presentation import schedule_summary
        return dict(summary=aggregate(rows), **facets, chart_trials=rows[:2000],
                    chart_total=len(rows), chart_sampled=len(rows)>2000,
                    schedule=schedule_summary(self, filters.get('run_id'),
                                              filters.get('provider'), filters.get('model'),
                                              filters.get('task_id'), snapshot=schedule_snapshot))

TERMINAL = {'PASS','FAIL','TIMEOUT','CANCELLED','ERROR','UNSUPPORTED','BLOCKED_EXTERNAL','INTERRUPTED'}

def aggregate(rows, grouped=True):
    rows = [r for r in rows if r['status'] in TERMINAL]
    n=len(rows); success=sum(r['status']=='PASS' for r in rows)
    wall=[r['wall_seconds'] for r in rows if r.get('wall_seconds') is not None]
    ttft=[r['ttft_seconds'] for r in rows if r.get('ttft_seconds') is not None]
    tokens=[r['input_tokens']+r['output_tokens'] for r in rows if r.get('input_tokens') is not None and r.get('output_tokens') is not None]
    costs=[r['cost_usd'] for r in rows if r.get('cost_usd') is not None]
    calls=sum(r['tool_calls'] for r in rows); failed=sum(r['failed_tool_calls'] for r in rows)
    full_cost = sum(costs) if n and len(costs)==n else None
    out=dict(trials=n,successes=success,completion_rate=success/n if n else None,
      total_failures=n-success,timeout_rate=sum(r['status']=='TIMEOUT' for r in rows)/n if n else None,
      tool_failure_frequency=failed/calls if calls else None, total_tool_calls=calls, failed_tool_calls=failed,
      median_wall_seconds=statistics.median(wall) if wall else None,
      p95_wall_seconds=sorted(wall)[max(0,math.ceil(.95*len(wall))-1)] if wall else None,
      median_ttft_seconds=statistics.median(ttft) if ttft else None,
      mean_tokens=statistics.mean(tokens) if tokens else None,median_tokens=statistics.median(tokens) if tokens else None,
      total_spend_usd=full_cost, measured_spend_usd=sum(costs) if costs else None,
      cost_per_success_usd=full_cost/success if full_cost is not None and success else None,
      wall_stddev_seconds=statistics.stdev(wall) if len(wall)>1 else None,
      measured_cost_trials=len(costs), measured_token_trials=len(tokens), measured_ttft_trials=len(ttft))
    out['status_counts'] = dict(Counter(r['status'] for r in rows))
    out['actual_cost_trials'] = sum(r.get('cost_usd') is not None and r.get('cost_source') == 'provider.usage.cost' for r in rows)
    out['estimated_cost_trials'] = sum(r.get('cost_usd') is not None and 'estimated' in (r.get('cost_source') or '') for r in rows)
    partial=[r['known_cost_subtotal_usd'] for r in rows
             if r.get('cost_usd') is None and r.get('known_cost_subtotal_usd') is not None]
    out['known_spend_usd']=sum(costs)+sum(partial) if costs or partial else None
    out['partial_cost_trials']=len(partial)
    for field, coverage in [('input_tokens','input_token'), ('output_tokens','output_token'), ('cached_input_tokens','cached_input_token')]:
        values = [r[field] for r in rows if r.get(field) is not None]
        out['observed_'+field] = sum(values) if values else None
        out['measured_'+coverage+'_trials'] = len(values)
    if grouped:
        out['categories']={c:aggregate([r for r in rows if r['category']==c],False) for c in sorted({r['category'] for r in rows})}
        fields=('runner','provider','model','config_hash','corpus_hash')
        keys=sorted({tuple(r.get(f) for f in fields) for r in rows},key=lambda k:tuple(v or '' for v in k))
        out['groups']=[dict(zip(fields,k)) | aggregate([r for r in rows if tuple(r.get(f) for f in fields)==k],False) for k in keys]
    return out

def export_data(rows, format):
    if format=='json':
        return json.dumps(rows,indent=2)
    s=io.StringIO()
    fields=sorted({k for r in rows for k in r})
    w=csv.DictWriter(s,fieldnames=fields); w.writeheader()
    for r in rows:
        values={k:json.dumps(v) if isinstance(v,(dict,list,bool)) else '' if v is None else v for k,v in r.items()}
        # Spreadsheet formula injection protection, documented in export format.
        w.writerow({k:"'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v for k,v in values.items()})
    return s.getvalue()
