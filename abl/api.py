"""Read-only loopback results API and same-origin dashboard."""
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .store import Store,aggregate,export_data
from . import __version__
import json
import os
import stat
from typing import Any
from pydantic import BaseModel, Field


class TrialPageResponse(BaseModel):
    items: list[dict[str, str | int | float | bool | None]]
    total: int = Field(ge=0)
    limit: int = Field(ge=1,le=200)
    offset: int = Field(ge=0)


class OverviewResponse(BaseModel):
    summary: dict[str, Any]
    providers: list[str]
    models: list[str]
    tasks: list[str]
    chart_trials: list[dict[str, str | int | float | bool | None]]
    chart_total: int = Field(ge=0)
    chart_sampled: bool


def read_trace(root, tid):
    result={'trace':[], 'trace_truncated':False, 'trace_error':None}
    path=root/'artifacts'/tid/'trace.jsonl'
    try:
        for p in (root/'artifacts',path.parent,path):
            if p.is_symlink(): raise ValueError('Evidence symlinks are not supported')
        with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
                raise ValueError('Trace must be a regular file')
            remaining=2_000_000
            while remaining>0:
                line=f.readline(min(remaining+1,1_000_001))
                if not line: break
                if len(line)>remaining or len(line)>1_000_000:
                    result['trace_truncated']=True; break
                remaining-=len(line)
                try: result['trace'].append(json.loads(line))
                except (ValueError,UnicodeDecodeError):
                    result['trace_error']='Trace contains an incomplete or invalid event'; break
            if remaining==0 and f.read(1): result['trace_truncated']=True
    except FileNotFoundError: pass
    except (OSError,ValueError) as error: result['trace_error']=str(error)
    return result

def create_app(root):
    app=FastAPI(title='Agent Benchmark Lab',version=__version__)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','[::1]'])
    @app.middleware('http')
    async def local_response(request: Request, call_next):
        origin = request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            response = JSONResponse({'detail':'Foreign origin is not allowed'}, status_code=403)
        else:
            response = await call_next(request)
        response.headers.update({
            'Cache-Control': 'no-store',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'Referrer-Policy': 'no-referrer',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        })
        return response
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
    @app.get('/api/trials/page',response_model=TrialPageResponse)
    def trial_page(limit:int=Query(100,ge=1,le=200),offset:int=Query(0,ge=0),
                   run_id:str|None=None,model:str|None=None,provider:str|None=None,task_id:str|None=None):
        return store.trial_page(limit,offset,run_id=run_id,model=model,provider=provider,task_id=task_id)
    @app.get('/api/overview',response_model=OverviewResponse)
    def overview(run_id:str|None=None,model:str|None=None,provider:str|None=None,task_id:str|None=None):
        return store.overview(run_id=run_id,model=model,provider=provider,task_id=task_id)
    @app.get('/api/trials/{tid}')
    def trial(tid:str):
        found=store.trials(id=tid)
        if not found: raise HTTPException(404,'Trial not found')
        from .models import validate_run_id
        try: validate_run_id(tid)
        except ValueError: raise HTTPException(400,'Invalid trial ID')
        t=found[0]
        t.update(read_trace(store.root,tid))
        return t
    @app.get('/api/export')
    def export(format:str='json',run_id:str|None=None,model:str|None=None,provider:str|None=None,task_id:str|None=None):
        if format not in ('json','csv'): raise HTTPException(400,'Use json or csv')
        return Response(export_data(rows(run_id,model,provider,task_id),format),media_type='application/json' if format=='json' else 'text/csv',headers={'Content-Disposition':f'attachment; filename="abl-results.{format}"'})
    static=Path(__file__).parent/'static'
    if static.exists(): app.mount('/',StaticFiles(directory=static,html=True),name='dashboard')
    return app
