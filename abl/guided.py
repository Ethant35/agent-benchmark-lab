"""Human-readable, free-first CLI. Author: Ethan.

The existing JSON CLI and execution/accounting contracts remain the source of truth.
"""
import hashlib
import os
import re
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time
from urllib.parse import urlencode

import typer
import yaml
from .models import Config, load_tasks, validate_run_id
from .store import Store, aggregate
from .isolation import BoundaryError, runtime_name
from .engine import run_suite

IMAGE = 'docker.io/library/python:3.12-slim'


def command(name, root, *args):
    return shlex.join(['abl', name, '--root', str(Path(root).resolve()), *args])


def workspace_info(root):
    return {'workspace_id': hashlib.sha256(str(Path(root).resolve()).encode()).hexdigest(),
            'start_command': command('start', root),
            'dashboard_command': command('dashboard', root)}


def setup_check(runtime='podman', image=IMAGE):
    """Inspect only. Never install, start, pull, reset or delete automatically."""
    good = True
    supported = sys.platform == 'darwin' and __import__('platform').machine() == 'arm64' and sys.version_info[:2] == (3, 12)
    typer.echo(f'Python {sys.version.split()[0]} · {sys.platform} · {__import__("platform").machine()}')
    if not supported:
        typer.echo('Note: the qualified target is macOS Apple Silicon with Python 3.12.')
    if not (Path(__file__).parent/'static/index.html').is_file():
        typer.echo('Dashboard missing. Reinstall the published wheel, which includes the dashboard.')
        good = False
    try:
        engine = runtime_name(runtime)
    except BoundaryError:
        typer.echo('Container engine is not ready. No task was started.')
        if not shutil.which('podman'):
            typer.echo('Install Podman for macOS: https://podman.io/docs/installation')
        else:
            typer.echo('Inspect existing machines: podman machine list')
            typer.echo('Start your existing machine: podman machine start NAME')
            typer.echo('If none exists: podman machine init --cpus 2 --memory 2048 --disk-size 12 abl-benchmark')
            typer.echo('Then: podman machine start abl-benchmark')
            typer.echo('If startup fails, inspect podman machine inspect NAME. Keep its data; do not reset or remove it.')
        typer.echo('After setup, run abl check again.')
        return False
    typer.echo(f'Container engine ready: {engine}')
    try:
        result = subprocess.run([engine, 'image', 'inspect', image, '--format', '{{.Id}}'],
                                capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        typer.echo('Image check failed. Check the engine connection, then run abl check again.')
        return False
    if result.returncode or not result.stdout.strip():
        typer.echo('Required image is missing. Download it once: '+shlex.join([engine, 'pull', image]))
        return False
    typer.echo('Task image ready. Candidate tasks run without network or host credentials.')
    return good


def read_config(path):
    try:
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            raise ValueError('expected a YAML mapping')
        if data.get('runner') == 'agent':
            required = ('provider', 'model', 'spend_limit_usd', 'input_price_per_million', 'output_price_per_million')
            missing = [key for key in required if data.get(key) is None]
            if missing: raise ValueError('model run needs explicit '+', '.join(missing))
        return Config.model_validate(data)
    except (OSError, ValueError, yaml.YAMLError) as error:
        # Validation errors may contain raw input. Do not echo configuration contents.
        if isinstance(error, ValueError) and str(error).startswith('model run needs explicit'):
            raise ValueError(str(error)) from None
        raise ValueError('Cannot read configuration. Use a valid YAML mapping with supported fields; run abl configure NEW_FILE to create one.') from None


def guided_config(path, root, resume):
    if resume is not None:
        validate_run_id(resume)
        if path: raise ValueError('Use --resume without --config; the saved configuration is required.')
        if not (root/'results.sqlite3').is_file(): raise ValueError('Results folder not found. Use the original --root.')
        store = Store(root)
        old = store.run(resume)
        if not old: raise ValueError('Run not found. Use abl runs with the original --root.')
        config = Config.model_validate(old['config'])
        if config.runner == 'agent' and any(t.get('cost_usd') is None for t in store.trials(run_id=resume)):
            raise ValueError('Earlier attempt has unknown cost. Review its generation records before any new spending; this run cannot safely resume.')
        return config
    return read_config(path) if path else Config(tasks=['bugfix-rounding'], runtime='podman')


def show_plan(config, root, resume=None):
    tasks = load_tasks()
    chosen = config.tasks or list(tasks)
    if any(t not in tasks for t in chosen): raise ValueError('Unknown task in configuration. See abl tasks list.')
    if config.runner == 'agent':
        if any(not char.isprintable() for value in (config.model, config.endpoint, config.api_key_env, config.reasoning_effort or '') for char in value):
            raise ValueError('Model, endpoint, credential variable and reasoning settings must not contain control characters.')
        if not re.fullmatch(r'[A-Z_][A-Z0-9_]*', config.api_key_env):
            raise ValueError('Credential environment variable must use uppercase letters, digits and underscores.')
        if not config.model.strip() or config.model == 'deterministic-reference':
            raise ValueError('Choose an explicit provider model ID.')
        if not config.supports_tools: raise ValueError('Model must support tools; declare supports_tools: true after checking its capabilities.')
        if config.input_price_per_million is None or config.output_price_per_million is None:
            raise ValueError('Set conservative input and output prices before a model run.')
    integration = all('integration' in tasks[tid][0].version.lower() for tid in chosen)
    model_kind = 'Model integration check' if integration else 'Model benchmark'
    typer.echo(model_kind if config.runner == 'agent' else f'Reference control · mode: {config.reference_mode} · No provider requests · $0 API cost')
    typer.echo('Results folder: '+str(root.resolve()))
    if resume: typer.echo('Resume saved run: '+resume+' (completed slots stay saved)')
    typer.echo(f'Tasks: {", ".join(chosen)} · {config.repeats} repeat(s) · {len(chosen)*config.repeats} scheduled trial(s)')
    for tid in chosen:
        task = tasks[tid][0]
        deadline = min(task.runtime_seconds, config.runtime_seconds or task.runtime_seconds)
        kind = 'integration contract' if 'integration' in task.version.lower() else 'benchmark contract'
        typer.echo(f'  {tid} v{task.version}: {deadline:g}s limit · {kind}')
    typer.echo('Configuration SHA256: '+config.fingerprint())
    if config.runner == 'agent':
        typer.echo(f'Provider: {config.provider} · Model: {config.model}')
        typer.echo('Endpoint: '+config.endpoint)
        typer.echo(f'Streaming: {config.streaming} · Reasoning: {config.reasoning_effort or "provider default"} · Temperature: {config.temperature if config.temperature is not None else "provider default"}')
        typer.echo(f'Tool-step cap: {config.max_tool_steps if config.max_tool_steps is not None else "task contract"} · Token budget: {config.token_budget if config.token_budget is not None else "task contract / request caps"}')
        typer.echo(f'Per trial: at most {config.max_requests} requests, {config.max_output_tokens} output tokens/request.')
        typer.echo(f'Whole-run spending reserve: ${config.spend_limit_usd:g} USD, including earlier attempts when resuming.')
        typer.echo(f'Configured price bounds per million tokens: input ${config.input_price_per_million:g}, output ${config.output_price_per_million:g}.')
        typer.echo('This local reserve uses your price bounds; it is not a provider billing cap. Use a provider-side cap for a hard limit.')
        typer.echo('Unknown charges stop further spending. Requests are never retried automatically.')
        typer.echo('Task text and tool results go to the selected provider. Credentials stay on the host.')
    return chosen


class Progress:
    """Only status metadata reaches the terminal, never model or tool payloads."""
    def __init__(self, root):
        self.root = root
        self.run_id = None
        self.started = time.monotonic()

    def __call__(self, event):
        kind = event['kind']
        elapsed = time.monotonic()-self.started
        if kind == 'run_started':
            self.run_id = event['run_id']
            typer.echo('Run '+self.run_id)
            typer.echo('Cancel safely: Ctrl+C, or '+command('cancel', self.root, self.run_id))
        elif kind == 'trial_started':
            typer.echo(f'[{elapsed:.1f}s] {event["task_id"]}: preparing isolated workspace')
        elif kind == 'request_started':
            typer.echo(f'[{elapsed:.1f}s] Waiting for provider response…')
        elif kind == 'tool':
            typer.echo(f'[{elapsed:.1f}s] Tool step completed')
        elif kind == 'trial_finished':
            typer.echo(f'[{elapsed:.1f}s] {event["task_id"]}: {event["status"]}')
        elif kind == 'verifier':
            typer.echo(f'[{elapsed:.1f}s] Independent verifier completed')


def finish_summary(root, rid):
    store = Store(root)
    trials = store.trials(run_id=rid)
    summary = aggregate(trials)
    typer.echo(f'Result: {summary["successes"]}/{summary["trials"]} passed · run {store.run(rid)["status"]}')
    from .presentation import schedule_summary
    schedule = schedule_summary(store, rid)
    if schedule and schedule['tasks'] is not None:
        typer.echo(f'Schedule: {schedule["passed"]}/{schedule["tasks"]} passed · {schedule["recovered"]} recovered · {schedule["failed"]} failed · {schedule["incomplete"] + schedule["pending"]} incomplete · {schedule["unknown"]} unknown')
    else:
        typer.echo('Schedule: outcome unavailable for this legacy run; attempt history is shown below.')
    if summary['total_spend_usd'] is None:
        known = summary['known_spend_usd']
        detail = f'Known subtotal: ${known:.9f} USD.' if known is not None else 'No settled cost subtotal is available.'
        typer.echo('Total cost: unknown. '+detail+' Review the saved evidence.')
    else:
        qualifier = 'includes estimates' if summary['estimated_cost_trials'] else 'recorded'
        typer.echo(f'Total cost: ${summary["total_spend_usd"]:.9f} USD ({qualifier}).')
    if trials and all(t['runner'] == 'reference' for t in trials):
        typer.echo('Reference controls check the runner and verifier. They are not model scores.')
    for trial in trials:
        if trial['status'] != 'PASS':
            typer.echo(f'  {trial["task_id"]}: {trial["status"]} · {trial.get("failure_category") or "see evidence"}')
    typer.echo('Inspect: '+command('inspect', root, rid))
    typer.echo('Open results: '+command('dashboard', root))
    typer.echo('Then visit http://127.0.0.1:8765/?'+urlencode({'run_id': rid}))
    return all(t['status'] == 'PASS' for t in trials) and bool(trials)


def start(root, path=None, resume=None, plan=False, accept_cost=None):
    root = root.resolve()
    try:
        config = guided_config(path, root, resume)
        show_plan(config, root, resume)
        if plan: return
        if config.runner == 'agent':
            if accept_cost is not None:
                if accept_cost != config.spend_limit_usd:
                    raise ValueError('--accept-cost must equal the saved whole-run spending reserve exactly.')
            elif not typer.confirm('Start this model run and accept the stated spending reserve?', default=False):
                typer.echo('No run started.'); return
        elif accept_cost is not None:
            raise ValueError('--accept-cost applies only to a model configuration.')
        if not setup_check(config.runtime, config.image): raise typer.Exit(2)
        entered_key = False
        if config.runner == 'agent' and not os.environ.get(config.api_key_env):
            if not sys.stdin.isatty():
                raise ValueError(f'Credential missing: set {config.api_key_env} in this process environment, or run interactively for hidden input.')
            value = typer.prompt(f'{config.api_key_env} (hidden, used for this run only)', hide_input=True)
            if not value.strip(): raise ValueError('Credential is empty. No run started.')
            os.environ[config.api_key_env] = value
            entered_key = True
        progress = Progress(root)
        try:
            rid = run_suite(root, config, resume, observer=progress)
        except KeyboardInterrupt:
            typer.echo('Run interrupted. Cleanup was attempted; saved evidence is retained.')
            if progress.run_id:
                typer.echo('Review: '+command('inspect', root, progress.run_id))
                typer.echo('Resume only this saved schedule: '+command('start', root, '--resume', progress.run_id))
            raise typer.Exit(130)
        finally:
            if entered_key: os.environ.pop(config.api_key_env, None)
        passed = finish_summary(root, rid)
        if not resume and config.runner == 'reference':
            typer.echo('Optional model run: abl configure model.yaml, then '+command('start', root, '--config', 'model.yaml'))
        if not passed: raise typer.Exit(1)
    except (ValueError, OSError, BoundaryError) as error:
        typer.echo('Cannot start: '+str(error), err=True)
        raise typer.Exit(2) from None


def configure(output):
    if output.exists() or output.is_symlink():
        raise typer.BadParameter('File already exists. Choose a new path; existing settings will not be overwritten.')
    provider = typer.prompt('Provider (openrouter or openai-compatible)', default='openrouter')
    if provider not in ('openrouter', 'openai-compatible'): raise typer.BadParameter('Unsupported provider')
    model = typer.prompt('Exact model ID').strip()
    if not model or model == 'deterministic-reference': raise typer.BadParameter('Enter an exact provider model ID')
    endpoint = 'https://openrouter.ai/api/v1'
    key_env = 'OPENROUTER_API_KEY'
    if provider == 'openai-compatible':
        typer.echo('Other compatible endpoints are implemented but not qualified on this release.')
        endpoint = typer.prompt('Endpoint URL')
        key_env = typer.prompt('Credential environment variable', default='MODEL_API_KEY')
    cap = typer.prompt('Whole-run spending reserve in USD', default=0.05, type=float)
    typer.echo('Use current conservative price bounds for your selected model and endpoint.')
    input_price = typer.prompt('Input price per million tokens (USD)', type=float)
    output_price = typer.prompt('Output price per million tokens (USD)', type=float)
    if not typer.confirm('Have you checked that this model supports tool calls?', default=False):
        typer.echo('No configuration written. Check model capabilities first.'); return
    try:
        config = Config(runner='agent', provider=provider, model=model, endpoint=endpoint, api_key_env=key_env,
                        spend_limit_usd=cap, input_price_per_million=input_price,
                        output_price_per_million=output_price, supports_tools=True, streaming=True,
                        stream_usage=True, max_requests=8, max_output_tokens=1024,
                        tasks=['bugfix-rounding'], runtime='podman')
        # Exclusive creation keeps a concurrent file or symlink intact.
        with os.fdopen(os.open(output, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600), 'w') as f:
            f.write('# Author: Ethan\n# No credential values belong in this file.\n')
            f.write(yaml.safe_dump(config.model_dump(), sort_keys=False))
    except (ValueError, OSError):
        raise typer.BadParameter('Could not save configuration. Check numeric limits, endpoint, and a new writable output path.') from None
    typer.echo('Saved '+str(output.resolve())+'. No provider request was made.')
    typer.echo('Preview: '+shlex.join(['abl', 'start', '--config', str(output), '--plan']))
