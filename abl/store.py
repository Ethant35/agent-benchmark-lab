"""SQLite persistence, atomic state transitions, and denominator-aware reports."""
import csv
import io
import json
import math
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat()

class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, status TEXT, created_at TEXT, config TEXT, cancel INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS trials(id TEXT PRIMARY KEY, run_id TEXT NOT NULL, slot INTEGER NOT NULL, data TEXT NOT NULL);
            ''')
    def connect(self):
        db = sqlite3.connect(self.root/'results.sqlite3', timeout=30)
        db.row_factory = sqlite3.Row
        return db
    def create_run(self, rid, config):
        with self.connect() as db:
            db.execute('INSERT INTO runs VALUES(?,?,?,?,0)', (rid,'RUNNING',now(),json.dumps(config)))
    def runs(self):
        with self.connect() as db:
            return [{**dict(r), 'config':json.loads(r['config'])} for r in db.execute('SELECT * FROM runs ORDER BY created_at DESC')]
    def run(self, rid):
        return next((r for r in self.runs() if r['id']==rid), None)
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
        with self.connect() as db:
            rows = [json.loads(r[0]) for r in db.execute('SELECT data FROM trials ORDER BY rowid')]
        return [r for r in rows if all(not v or r.get(k)==v for k,v in filters.items())]

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
    if grouped:
        out['categories']={c:aggregate([r for r in rows if r['category']==c],False) for c in sorted({r['category'] for r in rows})}
        keys=sorted({(r['runner'],r['provider'],r['model'],r['config_hash']) for r in rows})
        out['groups']=[dict(zip(('runner','provider','model','config_hash'),k)) | aggregate([r for r in rows if (r['runner'],r['provider'],r['model'],r['config_hash'])==k],False) for k in keys]
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
