"""Consent/config tests never send a provider request. Author: Ethan."""
import json
import os
from pathlib import Path
from typer.testing import CliRunner
import yaml
from abl.cli import app
from abl.models import Config
from abl.store import Store

runner = CliRunner()

def test_start_help_and_free_plan(tmp_path):
    result = runner.invoke(app, ['start', '--root', str(tmp_path), '--plan'])
    assert result.exit_code == 0, result.output
    assert 'bugfix-rounding' in result.output
    assert 'No provider requests' in result.output
    assert not (tmp_path/'results.sqlite3').exists()

def model_config(tmp_path, **changes):
    data = dict(runner='agent', provider='openrouter', model='explicit/model', supports_tools=True,
                input_price_per_million=1, output_price_per_million=2, spend_limit_usd=.05,
                tasks=['bugfix-rounding'], max_requests=8, max_output_tokens=1024)
    data.update(changes)
    path=tmp_path/'model.yaml'; path.write_text(yaml.safe_dump(data)); return path

def test_reject_consent_without_starting_run(tmp_path):
    path=model_config(tmp_path)
    result=runner.invoke(app,['start','--root',str(tmp_path/'data'),'--config',str(path)],input='n\n')
    assert result.exit_code == 0, result.output
    assert 'explicit/model' in result.output and '$0.05' in result.output
    assert 'No run started' in result.output
    assert not (tmp_path/'data/results.sqlite3').exists()

def test_noninteractive_consent_must_match_exact_reserve(tmp_path):
    path=model_config(tmp_path)
    result=runner.invoke(app,['start','--root',str(tmp_path/'data'),'--config',str(path),'--accept-cost','0.01'])
    assert result.exit_code == 2
    assert 'must equal' in result.output
    assert not (tmp_path/'data/results.sqlite3').exists()

def test_missing_model_and_prices_fail_before_consent(tmp_path):
    path=tmp_path/'bad.yaml';path.write_text('runner: agent\nprovider: openrouter\n')
    result=runner.invoke(app,['start','--config',str(path),'--plan'])
    assert result.exit_code == 2
    assert 'model' in result.output

def test_invalid_yaml_is_readable(tmp_path):
    path=tmp_path/'bad.yaml';path.write_text('x: [')
    result=runner.invoke(app,['start','--config',str(path),'--plan'])
    assert result.exit_code == 2
    assert 'configuration' in result.output.lower()
    assert 'Traceback' not in result.output

def test_configure_cannot_overwrite(tmp_path):
    path=tmp_path/'model.yaml';path.write_text('original')
    result=runner.invoke(app,['configure',str(path)])
    assert result.exit_code == 2
    assert path.read_text()=='original'

def test_configure_no_key_saved(tmp_path):
    path=tmp_path/'model.yaml'
    result=runner.invoke(app,['configure',str(path)],input='openrouter\nexplicit/model\n0.05\n0.3\n1.2\ny\n')
    assert result.exit_code == 0, result.output
    c=Config.model_validate(yaml.safe_load(path.read_text()))
    assert c.model=='explicit/model' and c.provider=='openrouter'
    assert c.tasks==['bugfix-rounding'] and c.spend_limit_usd==.05
    assert c.supports_tools and c.max_requests==8 and c.max_output_tokens==1024
    assert path.stat().st_mode & 0o777 == 0o600

def test_resume_unknown_cost_is_blocked_before_runtime(tmp_path):
    store=Store(tmp_path);c=Config(runner='agent',provider='openrouter',model='x',supports_tools=True,
         input_price_per_million=1,output_price_per_million=2)
    rid='a'*32;store.create_run(rid,c.model_dump());store.state(rid,'INTERRUPTED')
    store.save(dict(id='b'*32,run_id=rid,slot=0,status='INTERRUPTED',cost_usd=None))
    result=runner.invoke(app,['start','--root',str(tmp_path),'--resume',rid,'--plan'])
    assert result.exit_code == 2
    assert 'unknown cost' in result.output.lower()

def test_check_missing_runtime_is_actionable_and_readonly(monkeypatch):
    from abl import guided
    from abl.isolation import BoundaryError
    def unavailable(runtime): raise BoundaryError('not ready')
    monkeypatch.setattr(guided, 'runtime_name', unavailable)
    monkeypatch.setattr(guided.shutil, 'which', lambda name:'/podman')
    result=runner.invoke(app,['check'])
    assert result.exit_code==2
    assert 'podman machine list' in result.output
    assert 'do not reset or remove' in result.output

def test_check_missing_image_returns_failure(monkeypatch):
    from abl import guided
    from types import SimpleNamespace
    monkeypatch.setattr(guided,'runtime_name',lambda name:'podman')
    monkeypatch.setattr(guided.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=1,stdout=''))
    result=runner.invoke(app,['check'])
    assert result.exit_code==2
    assert 'podman pull docker.io/library/python:3.12-slim' in result.output

def test_workspace_commands_preserve_spaces_and_identity(tmp_path):
    import shlex
    from fastapi.testclient import TestClient
    from abl.api import create_app
    root=tmp_path/'my results'
    with TestClient(create_app(root),base_url='http://localhost') as client:
        response=client.get('/api/workspace')
        assert response.status_code==200
        data=response.json()
        assert shlex.split(data['start_command'])==['abl','start','--root',str(root.resolve())]
        assert len(data['workspace_id'])==64
        assert client.post('/api/workspace').status_code==405
        assert client.get('/api/workspace',headers={'Origin':'https://other.invalid'}).status_code==403

def test_read_config_does_not_echo_raw_secrets(tmp_path):
    path=tmp_path/'bad.yaml';path.write_text('api_key: secret-sentinel\n')
    result=runner.invoke(app,['start','--config',str(path),'--plan'])
    assert result.exit_code==2
    assert 'secret-sentinel' not in result.output

def test_explicit_zero_reserve_never_accepted(tmp_path):
    path=model_config(tmp_path,spend_limit_usd=0)
    result=runner.invoke(app,['start','--config',str(path),'--plan'])
    assert result.exit_code==2

def test_reference_negative_control_is_named(tmp_path):
    path=tmp_path/'timeout.yaml';path.write_text('reference_mode: timeout\ntasks: [bugfix-rounding]\nruntime_seconds: 1\n')
    result=runner.invoke(app,['start','--config',str(path),'--plan'])
    assert result.exit_code==0
    assert 'mode: timeout' in result.output

def test_control_characters_cannot_hide_model_consent(tmp_path):
    path=model_config(tmp_path,model='explicit/model\x1b[2J')
    result=runner.invoke(app,['start','--config',str(path),'--plan'])
    assert result.exit_code==2
    assert '\x1b[2J' not in result.output

def test_missing_credential_after_consent_never_runs(tmp_path,monkeypatch):
    from abl import guided
    path=model_config(tmp_path)
    monkeypatch.delenv('OPENROUTER_API_KEY',raising=False)
    monkeypatch.setattr(guided,'setup_check',lambda *a: True)
    def forbidden(*args,**kwargs): raise AssertionError('Run started without credential')
    monkeypatch.setattr(guided,'run_suite',forbidden)
    result=runner.invoke(app,['start','--root',str(tmp_path/'data'),'--config',str(path),'--accept-cost','.05'])
    assert result.exit_code==2
    assert 'Credential missing' in result.output
    assert not (tmp_path/'data/results.sqlite3').exists()

def test_progress_never_echoes_tool_or_provider_payload(capsys,tmp_path):
    from abl.guided import Progress
    progress=Progress(tmp_path)
    progress({'kind':'request_started','raw_response':'private-sentinel'})
    progress({'kind':'tool','arguments':{'key':'private-sentinel'}})
    output=capsys.readouterr().out
    assert 'Waiting for provider' in output and 'Tool step' in output
    assert 'private-sentinel' not in output


def test_validate_labels_corpus_selection_and_schedule_counts(tmp_path):
    # Keep the legacy total while making a one-task configuration unambiguous.
    from abl.models import load_tasks
    total = len(load_tasks())
    for selected, repeats, count in [(['bugfix-rounding'], 3, 1), ([], 2, total)]:
        path = tmp_path / 'counts.yaml'
        path.write_text(yaml.safe_dump({'tasks': selected, 'repeats': repeats}))
        result = runner.invoke(app, ['validate', '--config', str(path)])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data['tasks'] == data['available_corpus_tasks'] == total
        assert data['tasks_scope'] == 'available corpus tasks (legacy field)'
        assert data['selected_tasks'] == count
        assert data['scheduled_trials'] == count * repeats
        plan = runner.invoke(app, ['start', '--config', str(path), '--plan'])
        assert plan.exit_code == 0, plan.output
        assert f'{count * repeats} scheduled trial(s)' in plan.output
    path.write_text('tasks: [unknown-task]\n')
    invalid = runner.invoke(app, ['validate', '--config', str(path)])
    assert invalid.exit_code == 2
    assert 'Unknown task' in invalid.output
