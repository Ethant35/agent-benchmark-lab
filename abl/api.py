"""Read-only loopback results API and same-origin dashboard."""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .store import Store,aggregate,export_data
from . import __version__
import json

def create_app(root):
    app=FastAPI(title='Agent Benchmark Lab',version=__version__)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','[::1]'])
    store=Store(root)
    def rows(run_id=None,model=None,provider=None,task_id=None):
        return store.trials(run_id=run_id,model=model,provider=provider,task_id=task_id)
    @app.get('/api/runs')
    def runs(): return store.runs()
    @app.get('/api/trials')
    def trials(run_id:str|None=None,model:str|None=None,provider:str|None=None,task_id:str|None=None):
        return rows(run_id,model,provider,task_id)
    @app.get('/api/summary')
    def summary(run_id:str|None=None,model:str|None=None,provider:str|None=None,task_id:str|None=None):
        return aggregate(rows(run_id,model,provider,task_id))
    @app.get('/api/trials/{tid}')
    def trial(tid:str):
        found=store.trials(id=tid)
        if not found: raise HTTPException(404,'Trial not found')
        t=found[0]; p=store.root/'artifacts'/tid/'trace.jsonl'
        t['trace']=[json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []
        return t
    @app.get('/api/export')
    def export(format:str='json',run_id:str|None=None,model:str|None=None,provider:str|None=None,task_id:str|None=None):
        if format not in ('json','csv'): raise HTTPException(400,'Use json or csv')
        return Response(export_data(rows(run_id,model,provider,task_id),format),media_type='application/json' if format=='json' else 'text/csv',headers={'Content-Disposition':f'attachment; filename="abl-results.{format}"'})
    static=Path(__file__).parent/'static'
    if static.exists(): app.mount('/',StaticFiles(directory=static,html=True),name='dashboard')
    return app
