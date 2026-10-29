"""Controlled records test matching rules; these are not model results."""
import hashlib
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from abl.api import create_app
from abl.comparison import outcome_kind
from abl.engine import manifest_hash
from abl.models import Config
from abl.store import Store


def seed(store, *, streaming, status='PASS', reason=None, cost=.01, version='1.0',
         task_hash='a' * 64, image='b' * 64, runner='agent', tasks=None):
    config = Config(runner=runner, provider='openrouter' if runner == 'agent' else 'none',
                    model='test-model' if runner == 'agent' else 'deterministic-reference',
                    supports_tools=True, streaming=streaming)
    rid = uuid.uuid4().hex
    manifest = {'schema_version': 1, 'image_id': image,
                'tasks': tasks or [{'id': 'rounding', 'version': version, 'sha256': task_hash}]}
    store.create_run(rid, config.model_dump(), manifest)
    store.state(rid, 'COMPLETED')
    row = dict(id=uuid.uuid4().hex, run_id=rid, slot=0, task_id='rounding', task_version=version,
               category='bug_fix', runner=runner, provider=config.provider, model=config.model,
               config_hash=config.fingerprint(), corpus_hash=manifest_hash(manifest),
               task_artifact_id=task_hash, fixture_hash='c' * 64, image_id=image, status=status,
               failure_category=reason, cost_usd=cost, known_cost_subtotal_usd=None,
               cost_source='provider.usage.cost', wall_seconds=2, tool_calls=1,
               verifier={'exit_code': 0 if status == 'PASS' else 1, 'stdout': 'private evidence'})
    store.save(row)
    return row


def compare(store, a, b, **filters):
    return store.compare(a['config_hash'], b['config_hash'], **filters)


def test_equivalent_task_compares_despite_different_corpus_selection(tmp_path):
    s = Store(tmp_path)
    a = seed(s, streaming=True)
    b = seed(s, streaming=False, tasks=[{'id': 'rounding', 'version': '1.0', 'sha256': 'a' * 64},
                                      {'id': 'other', 'version': '1.0', 'sha256': 'd' * 64}])
    assert a['corpus_hash'] != b['corpus_hash']
    r = compare(s, a, b)
    assert r['matched_tasks'] == 1
    assert r['differences'] == [{'setting': 'streaming', 'left': True, 'right': False}]
    assert r['matches'][0]['left']['evidence'][0]['id'] == a['id']
    assert 'private evidence' not in json.dumps(r)


@pytest.mark.parametrize('change', [{'version': '1.1'}, {'task_hash': 'd' * 64},
                                  {'image': 'e' * 64}, {'runner': 'reference'}])
def test_changed_contract_image_or_runner_cannot_match(tmp_path, change):
    s = Store(tmp_path); a = seed(s, streaming=True); b = seed(s, streaming=False, **change)
    r = compare(s, a, b)
    assert r['matched_tasks'] == 0
    assert r['excluded']['left']['no_equivalent_task'] == 1
    assert r['excluded']['right']['no_equivalent_task'] == 1


@pytest.mark.parametrize('field', ['corpus_hash', 'task_artifact_id', 'task_version', 'image_id', 'slot', 'model'])
def test_inconsistent_saved_identity_is_excluded(tmp_path, field):
    s = Store(tmp_path); a = seed(s, streaming=True); b = seed(s, streaming=False)
    b[field] = 'wrong'; s.save(b)
    r = compare(s, a, b)
    assert r['matched_tasks'] == 0
    assert r['excluded']['right']['unverified_identity'] == 1


def test_legacy_missing_manifest_and_nonterminal_are_explicit(tmp_path):
    s = Store(tmp_path); a = seed(s, streaming=True); b = seed(s, streaming=False)
    with s.connect() as db:
        db.execute('DELETE FROM run_manifests WHERE run_id=?', (b['run_id'],))
    assert compare(s, a, b)['excluded']['right']['unverified_identity'] == 1
    b['status'] = 'RUNNING'; s.save(b)
    assert compare(s, a, b)['excluded']['right']['nonterminal'] == 1


def test_all_retries_unknown_cost_and_failure_classes_are_preserved(tmp_path):
    s = Store(tmp_path)
    a = seed(s, streaming=True, status='INTERRUPTED', reason='process_lost', cost=None)
    a['known_cost_subtotal_usd'] = .003; s.save(a)
    retry = {**a, 'id': uuid.uuid4().hex, 'status': 'PASS', 'failure_category': None,
             'cost_usd': .007, 'known_cost_subtotal_usd': .005}
    s.save(retry)
    b = seed(s, streaming=False, status='ERROR', reason='verification_error')
    r = compare(s, a, b)['matches'][0]
    assert r['left']['attempts'] == 2 and r['left']['passes'] == 1
    assert r['left']['cost_usd'] is None
    assert r['left']['known_cost_subtotal_usd'] == pytest.approx(.01)
    assert r['cost_delta_usd'] is None
    assert r['left']['outcomes']['interrupted_or_cancelled'] == 1
    assert r['right']['outcomes']['harness_or_execution_error'] == 1
    assert len(s.trials()) == 3


def test_estimates_and_actual_charges_have_no_cost_delta(tmp_path):
    s = Store(tmp_path); a = seed(s, streaming=True); b = seed(s, streaming=False)
    b['cost_source'] = 'estimated'; s.save(b)
    assert compare(s, a, b)['matches'][0]['cost_delta_usd'] is None


def test_api_filters_validation_and_no_history_mutation(tmp_path):
    s = Store(tmp_path); a = seed(s, streaming=True); b = seed(s, streaming=False)
    before = hashlib.sha256(json.dumps(s.trials(), sort_keys=True).encode()).hexdigest()
    client = TestClient(create_app(tmp_path), base_url='http://localhost')
    params = {'left': a['config_hash'], 'right': b['config_hash']}
    assert client.get('/api/comparison', params=params).json()['matched_tasks'] == 1
    assert client.get('/api/comparison', params=params | {'task_id': 'absent'}).json()['matched_tasks'] == 0
    assert client.get('/api/comparison', params=params | {'run_id': a['run_id']}).json()['matched_tasks'] == 0
    assert client.get('/api/comparison', params=params | {'provider': 'none'}).json()['matched_tasks'] == 0
    assert client.get('/api/comparison', params=params | {'left': 'bad'}).status_code == 422
    assert client.get('/api/comparison', params=params | {'right': a['config_hash']}).status_code == 400
    assert hashlib.sha256(json.dumps(s.trials(), sort_keys=True).encode()).hexdigest() == before


def test_active_run_keeps_terminal_cost_scope_explicit(tmp_path):
    s = Store(tmp_path); a = seed(s, streaming=True); b = seed(s, streaming=False)
    s.state(a['run_id'], 'RUNNING')
    assert compare(s, a, b)['matches'][0]['left']['active_run'] is True


def test_verifier_rejection_does_not_claim_model_fault():
    assert outcome_kind({'status': 'FAIL', 'failure_category': 'verification_failed'}) == 'verifier_rejected_cause_unresolved'
    assert outcome_kind({'status': 'TIMEOUT', 'failure_category': 'runtime_limit'}) == 'configured_limit'
    assert outcome_kind({'status': 'ERROR', 'failure_category': 'provider_error'}) == 'provider_error'


def test_evidence_limit_preserves_full_attempt_totals_and_timing_coverage(tmp_path):
    s = Store(tmp_path); a = seed(s, streaming=True); b = seed(s, streaming=False)
    for _ in range(100):
        s.save({**a, 'id': uuid.uuid4().hex, 'wall_seconds': None})
    r = compare(s, a, b)['matches'][0]['left']
    assert r['attempts'] == 101 and r['passes'] == 101
    assert r['cost_usd'] == pytest.approx(1.01)
    assert r['measured_wall_attempts'] == 1
    assert r['evidence_sampled'] is True and len(r['evidence']) == 100


def test_endpoint_difference_is_reported_without_disclosing_value(tmp_path):
    s = Store(tmp_path); a = seed(s, streaming=True); b = seed(s, streaming=False)
    run = s.run(b['run_id']); run['config']['endpoint'] = 'https://private.example/v1'
    b['config_hash'] = hashlib.sha256(json.dumps(run['config'], sort_keys=True).encode()).hexdigest()
    with s.connect() as db:
        db.execute('UPDATE runs SET config=? WHERE id=?', (json.dumps(run['config']), b['run_id']))
    s.save(b)
    r = compare(s, a, b)
    assert r['matched_tasks'] == 1
    assert {'setting': 'endpoint', 'left': '[withheld]', 'right': '[withheld]'} in r['differences']
    assert 'private.example' not in json.dumps(r)
