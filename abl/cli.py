"""Public command line interface. No implicit provider spending."""
import json
from pathlib import Path
from typing import Annotated
import typer
import yaml
from .models import Config, load_tasks, validate_run_id
from .store import Store, aggregate, export_data
from .isolation import runtime_name, BoundaryError
from .engine import run_suite

app=typer.Typer(no_args_is_help=True,help='Reproducible isolated agent benchmarks. Author: Ethan.')
tasks_app=typer.Typer(no_args_is_help=True); app.add_typer(tasks_app,name='tasks')
Root=Annotated[Path,typer.Option('--root',help='Benchmark data directory')]

def emit(x): typer.echo(json.dumps(x,indent=2))
def config_at(path): return Config.model_validate(yaml.safe_load(path.read_text()) or {}) if path else Config()

@app.command()
def init(root:Root=Path('.abl')):
    Store(root); config=root/'config.yaml'
    if not config.exists(): config.write_text(yaml.safe_dump(Config().model_dump(),sort_keys=False))
    emit({'root':str(root.resolve()),'config':str(config),'author':'Ethan'})

@app.command()
def doctor(runtime:str='auto'):
    import os,sys,subprocess
    try:
        engine=runtime_name(runtime)
        image=subprocess.run([engine,'image','inspect','docker.io/library/python:3.12-slim','--format','{{.Id}}'],capture_output=True,text=True)
        emit({'python':sys.version.split()[0],'runtime':engine,'image':image.stdout.strip() or 'missing: pull docker.io/library/python:3.12-slim',
            'openrouter_credential_present':bool(os.environ.get('OPENROUTER_API_KEY')),'dashboard_built':(Path(__file__).parent/'static/index.html').exists(),
            'host_execution_fallback':False})
    except BoundaryError as e:
        emit({'status':'BLOCKED_EXTERNAL','detail':str(e)}); raise typer.Exit(2)

@app.command()
def providers():
    emit([{'id':'openrouter','endpoint':'https://openrouter.ai/api/v1','tools':'explicit capability required','usage':'native metadata or unavailable','streaming':'SSE'},
        {'id':'openai-compatible','endpoint':'configurable HTTPS or loopback','tools':'explicit capability required','usage':'endpoint-dependent','streaming':'optional OpenAI SSE dialect'}])

@tasks_app.command('list')
def list_tasks(): emit([t.model_dump() for t,p in load_tasks().values()])

@tasks_app.command('inspect')
def inspect_task(task_id:str):
    tasks=load_tasks()
    if task_id not in tasks: raise typer.BadParameter('Unknown task')
    emit(tasks[task_id][0].model_dump())

@app.command()
def validate(config:Annotated[Path|None,typer.Option('--config')]=None):
    c=config_at(config); tasks=load_tasks()
    if any(t not in tasks for t in c.tasks): raise typer.BadParameter('Unknown task in configuration')
    emit({'valid':True,'tasks':len(tasks),'categories':sorted({t.category for t,p in tasks.values()}),'config_hash':c.fingerprint()})

@app.command()
def run(root:Root=Path('.abl'),config:Annotated[Path|None,typer.Option('--config')]=None,
        task:Annotated[list[str]|None,typer.Option('--task')]=None,
        repeats:Annotated[int|None,typer.Option('--repeats')]=None,
        resume:Annotated[str|None,typer.Option('--resume')]=None):
    if resume is not None:
        try: validate_run_id(resume)
        except ValueError as e: raise typer.BadParameter(str(e)) from e
    if resume is not None and not config:
        old=Store(root).run(resume)
        if not old: raise typer.BadParameter('Run not found')
        c=Config.model_validate(old['config'])
    else: c=config_at(config)
    data=c.model_dump()
    if task: data['tasks']=task
    if repeats is not None: data['repeats']=repeats
    c=Config.model_validate(data)
    try:
        rid=run_suite(root,c,resume)
    except (BoundaryError,ValueError) as e:
        emit({'error':str(e)}); raise typer.Exit(2)
    outcomes=Store(root).trials(run_id=rid)
    if any(t['status']!='PASS' for t in outcomes): raise typer.Exit(1)

@app.command()
def runs(root:Root=Path('.abl')): emit(Store(root).runs())

@app.command()
def inspect(run_id:str,root:Root=Path('.abl')):
    store=Store(root); run=store.run(run_id)
    if not run: raise typer.BadParameter('Run not found')
    emit({'run':run,'trials':store.trials(run_id=run_id)})

@app.command()
def compare(root:Root=Path('.abl'),run_id:Annotated[str|None,typer.Option('--run-id')]=None):
    emit(aggregate(Store(root).trials(run_id=run_id)))

@app.command()
def report(output:Annotated[Path,typer.Argument()]=Path('report.html'),root:Root=Path('.abl'),run_id:Annotated[str|None,typer.Option('--run-id')]=None):
    import html
    rows=Store(root).trials(run_id=run_id); summary=aggregate(rows)
    content='<!doctype html><meta charset="utf-8"><meta name="author" content="Ethan"><title>Agent Benchmark Lab report</title><style>body{font:16px system-ui;max-width:1000px;margin:3rem auto}pre{white-space:pre-wrap}</style><h1>Agent Benchmark Lab</h1><p>Reference results are infrastructure checks, not model scores. Unknown measurements remain unavailable.</p><h2>Summary</h2><pre>'+html.escape(json.dumps(summary,indent=2))+'</pre><h2>Trial evidence</h2><pre>'+html.escape(json.dumps(rows,indent=2))+'</pre>'
    output.write_text(content); emit({'report':str(output.resolve())})

@app.command()
def export(output:Path,format:Annotated[str,typer.Option('--format')]='json',root:Root=Path('.abl'),run_id:Annotated[str|None,typer.Option('--run-id')]=None):
    if format not in ('json','csv'): raise typer.BadParameter('Use json or csv')
    output.write_text(export_data(Store(root).trials(run_id=run_id),format)); emit({'export':str(output.resolve())})

@app.command()
def dashboard(root:Root=Path('.abl'),port:int=8765):
    import uvicorn
    from .api import create_app
    if not (Path(__file__).parent/'static/index.html').exists(): raise typer.BadParameter('Dashboard missing. Reinstall the published wheel (dashboard included). Source contributors: npm ci --prefix dashboard && npm run build --prefix dashboard')
    uvicorn.run(create_app(root),host='127.0.0.1',port=port)

@app.command()
def cancel(run_id:str,root:Root=Path('.abl')):
    store=Store(root); old=store.run(run_id)
    if not old: raise typer.BadParameter('Run not found')
    if old['status']!='RUNNING': raise typer.BadParameter('Run is not active')
    store.state(run_id,'CANCELLING',True); emit({'run_id':run_id,'cancellation_requested':True})


@app.command()
def backup(output:Path,root:Root=Path('.abl')):
    """Copy an idle store and its evidence to a new verified backup directory."""
    from .recovery import backup_store
    try: emit(backup_store(root,output))
    except (OSError,ValueError) as error: raise typer.BadParameter(str(error)) from error


@app.command()
def restore(backup:Path,root:Root):
    """Verify and restore a backup into a new directory; never overwrite data."""
    from .recovery import restore_store
    try: emit(restore_store(backup,root))
    except (OSError,ValueError) as error: raise typer.BadParameter(str(error)) from error


@app.command()
def diagnostics(root:Root=Path('.abl')):
    """Print operational counts without task, provider, path or config payloads."""
    from .recovery import diagnostics as report
    emit(report(Store(root)))


@app.command()
def check(runtime: str = 'podman'):
    """Check prerequisites with safe, readable recovery steps; make no changes."""
    from .guided import setup_check
    if runtime not in ('auto', 'podman', 'docker'): raise typer.BadParameter('Use podman, docker, or auto')
    if not setup_check(runtime): raise typer.Exit(2)


@app.command()
def start(root: Root = Path('.abl'),
          config: Annotated[Path | None, typer.Option('--config')] = None,
          resume: Annotated[str | None, typer.Option('--resume')] = None,
          plan: Annotated[bool, typer.Option('--plan', help='Preview only; no setup or requests')] = False,
          accept_cost: Annotated[float | None, typer.Option('--accept-cost', help='Explicit noninteractive consent; must equal the configured USD reserve')] = None):
    """Run one free reference task, or review and consent to a selected model config."""
    from .guided import start as guided_start
    guided_start(root, config, resume, plan, accept_cost)


@app.command()
def configure(output: Path):
    """Create a model config with explicit provider, model, prices and spending reserve."""
    from .guided import configure as guided_configure
    guided_configure(output)
