"""Persisted API contracts; no provider requests or candidate execution."""
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from abl.api import create_app
from abl.store import Store, aggregate


def record(index, **overrides):
    return dict(id=f'{index:032x}', run_id='a'*32, slot=index,
                runner='agent', provider='openrouter', model='example',
                task_id='task', task_version='1', category='navigation',
                config_hash='config', status='PASS', wall_seconds=2,
                ttft_seconds=None, input_tokens=10, output_tokens=2,
                cached_input_tokens=4, cost_usd=.01,
                cost_source='provider.usage.cost', tool_calls=1,
                failed_tool_calls=0, verifier={'stdout': 'private evidence'},
                provider_requests=[{'raw': 'private response'}],
                **{}) | overrides


@pytest.fixture
def history(tmp_path):
    store = Store(tmp_path)
    store.create_run('a'*32, {'runner': 'agent'})
    # More than the chart cap, with a large payload that list responses must omit.
    records = [record(i, verifier={'stdout': 'x'*4096}) for i in range(2005)]
    records += [record(2005, status='RUNNING', model='other'),
                record(2006, status='FAIL', cost_usd=None, input_tokens=None,
                       cached_input_tokens=None)]
    with store.connect() as db:
        db.executemany('INSERT INTO trials VALUES(?,?,?,?)',
                       [(r['id'], r['run_id'], r['slot'], json.dumps(r)) for r in records])
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1') as client:
        yield store, client


def test_compact_pages_preserve_filters_order_and_total(history):
    _, client = history
    response = client.get('/api/trials/page?limit=2&offset=1&model=example')
    assert response.status_code == 200
    page = response.json()
    assert (page['total'], page['limit'], page['offset']) == (2006, 2, 1)
    assert [r['id'] for r in page['items']] == [f'{2004:032x}', f'{2003:032x}']
    assert all('verifier' not in r and 'provider_requests' not in r for r in page['items'])
    assert len(response.content) < 5000
    assert client.get('/api/trials/page', params={'model': "' OR 1=1 --"}).json()['total'] == 0


def test_overview_uses_all_terminal_trials_and_labels_recent_sample(history):
    _, client = history
    data = client.get('/api/overview?model=example').json()
    summary = data['summary']
    assert summary['trials'] == 2006
    assert summary['successes'] == 2005
    assert summary['status_counts'] == {'PASS': 2005, 'FAIL': 1}
    assert summary['total_spend_usd'] is None
    assert summary['actual_cost_trials'] == 2005
    assert summary['estimated_cost_trials'] == 0
    assert summary['observed_input_tokens'] == 20050
    assert summary['measured_input_token_trials'] == 2005
    assert summary['observed_output_tokens'] == 4012
    assert summary['measured_output_token_trials'] == 2006
    assert len(data['chart_trials']) == 2000
    assert data['chart_total'] == 2006 and data['chart_sampled'] is True
    assert data['chart_trials'][0]['id'] == f'{2006:032x}'
    assert data['models'] == ['example', 'other']  # Facets are not narrowed by filters.


@pytest.mark.parametrize('query', ['limit=0', 'limit=201', 'offset=-1', 'limit=abc'])
def test_page_rejects_invalid_bounds(tmp_path, query):
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1') as client:
        assert client.get('/api/trials/page?'+query).status_code == 422


def test_legacy_evidence_and_empty_overview_remain_available(tmp_path):
    store = Store(tmp_path)
    store.save(record(1))
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1') as client:
        assert client.get('/api/trials').json()[0]['verifier']['stdout'] == 'private evidence'
        assert client.get('/api/trials/'+f'{1:032x}').json()['provider_requests']
        data = client.get('/api/overview?model=missing').json()
        assert data['chart_trials'] == [] and data['summary']['trials'] == 0
        assert data['summary']['total_spend_usd'] is None
        assert data['chart_sampled'] is False


def test_connection_scope_commits_and_closes_even_on_failure(tmp_path):
    store = Store(tmp_path)
    with store.connect() as db:
        db.execute("INSERT INTO runs VALUES('ok','RUNNING','now','{}',0)")
    with pytest.raises(sqlite3.ProgrammingError):
        db.execute('SELECT 1')
    with pytest.raises(RuntimeError):
        with store.connect() as db:
            db.execute("INSERT INTO runs VALUES('rollback','RUNNING','now','{}',0)")
            raise RuntimeError('abort')
    assert store.run('ok') and store.run('rollback') is None


def test_cost_sources_are_not_mislabeled_as_provider_measurements():
    summary = aggregate([record(1), record(2, cost_source='estimated request reserves'),
                         record(3, cost_source='no_provider_requests', cost_usd=0),
                         record(4, cost_source='unavailable', cost_usd=None)])
    assert summary['actual_cost_trials'] == 1
    assert summary['estimated_cost_trials'] == 1
    assert summary['measured_cost_trials'] == 3


def test_local_dashboard_blocks_foreign_origins_and_does_not_cache(tmp_path):
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1') as client:
        for path in ['/api/runs', '/api/not-found', '/']:
            response = client.get(path)
            assert response.headers['cache-control'] == 'no-store'
            assert response.headers['x-content-type-options'] == 'nosniff'
            assert "frame-ancestors 'none'" in response.headers['content-security-policy']
        assert client.get('/api/runs', headers={'Origin':'https://foreign.example'}).status_code == 403
        assert client.get('/api/runs', headers={'Origin':'http://127.0.0.1'}).status_code == 200
        assert client.get('/api/runs', headers={'Host':'foreign.example'}).status_code == 400


def test_additive_api_schemas_expose_bounded_page_contract(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        schema=client.get('/openapi.json').json()
        response=schema['paths']['/api/trials/page']['get']['responses']['200']['content']['application/json']['schema']
        assert '$ref' in response
        page=schema['components']['schemas'][response['$ref'].split('/')[-1]]
        assert set(page['required'])=={'items','total','limit','offset'}
        assert page['properties']['limit']['maximum']==200
