"""Persistent data safety and minimal diagnostics. Author: Ethan."""
import json
import os
import sqlite3
import stat
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from abl.api import create_app
from abl.store import Store, aggregate
from test_api_history import record


def test_new_store_is_private_even_with_open_umask(tmp_path):
    prior=os.umask(0)
    try:
        root=tmp_path/'private'; store=Store(root); store.save(record(1))
    finally: os.umask(prior)
    assert stat.S_IMODE(root.stat().st_mode)==0o700
    assert stat.S_IMODE((root/'results.sqlite3').stat().st_mode)==0o600


def test_corruption_is_actionable_and_original_bytes_are_preserved(tmp_path):
    path=tmp_path/'results.sqlite3'; data=b'broken SQLite file'; path.write_bytes(data)
    with pytest.raises(ValueError,match='restore.*backup'):
        Store(tmp_path)
    assert path.read_bytes()==data


def test_trace_is_bounded_and_marks_truncation(tmp_path):
    store=Store(tmp_path); t=record(1); store.save(t)
    folder=tmp_path/'artifacts'/t['id']; folder.mkdir(parents=True)
    (folder/'trace.jsonl').write_text(json.dumps({'kind':'tool','text':'x'*2_000_001})+'\n')
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        response=client.get('/api/trials/'+t['id'])
        assert response.status_code==200
        assert len(response.content)<10000
        assert response.json()['trace_truncated'] is True
        assert response.json()['trace']==[]


def test_trace_symlink_cannot_read_outside_evidence(tmp_path):
    store=Store(tmp_path); t=record(1); store.save(t)
    secret=tmp_path/'private.jsonl'; secret.write_text('{"secret":"sensitive"}\n')
    folder=tmp_path/'artifacts'/t['id']; folder.mkdir(parents=True)
    (folder/'trace.jsonl').symlink_to(secret)
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        response=client.get('/api/trials/'+t['id'])
        assert 'sensitive' not in response.text
        assert response.json()['trace_error']


def test_corpus_identity_separates_comparison_groups():
    result=aggregate([record(1,corpus_hash='one'),record(2,corpus_hash='two'),record(3)])
    assert len(result['groups'])==3
    assert {g['corpus_hash'] for g in result['groups']}=={'one','two',None}


def test_backup_restore_and_safe_diagnostics(tmp_path):
    from abl.recovery import backup_store, restore_store, diagnostics
    store=Store(tmp_path/'source'); t=record(1,artifact_dir='/private/location'); store.save(t)
    store.create_run('a'*32,{'endpoint':'https://private.example'})
    store.state('a'*32,'COMPLETED')
    folder=store.root/'artifacts'/t['id']; folder.mkdir(parents=True)
    (folder/'trace.jsonl').write_text('{"private":"task contents"}\n')
    backup=tmp_path/'backup'; backup_store(store.root,backup)
    restored=tmp_path/'restore'; restore_store(backup,restored)
    assert Store(restored).trials()==[t]
    assert (restored/'artifacts'/t['id']/'trace.jsonl').read_bytes()==(folder/'trace.jsonl').read_bytes()
    safe=json.dumps(diagnostics(store))
    assert all(secret not in safe for secret in ['private response','private evidence','private.example','/private/location','task contents'])
    with pytest.raises(ValueError,match='exist'):
        restore_store(backup,restored)
    (backup/'artifacts'/t['id']/'trace.jsonl').write_text('tampered')
    with pytest.raises(ValueError,match='checksum'):
        restore_store(backup,tmp_path/'tampered')


def test_activity_lock_blocks_backup_and_run_in_both_directions(tmp_path):
    from abl.recovery import store_lock,backup_store
    import abl.engine as engine
    from abl.models import Config
    source=tmp_path/'source';Store(source)
    with store_lock(source):
        with pytest.raises(ValueError,match='active'):
            backup_store(source,tmp_path/'backup')
    with store_lock(source,exclusive=True):
        with pytest.raises(ValueError,match='active'):
            engine.run_suite(source,Config())
    assert not (tmp_path/'backup').exists()


def test_incomplete_trial_retains_known_cost_in_summary():
    summary=aggregate([record(1),record(2,cost_usd=None,known_cost_subtotal_usd=.02)])
    assert summary['total_spend_usd'] is None
    assert summary['known_spend_usd']==pytest.approx(.03)
    assert summary['partial_cost_trials']==1


def test_legacy_root_becomes_private_without_rewriting_history(tmp_path):
    root=tmp_path/'legacy';root.mkdir(mode=0o755)
    store=Store(root);store.save(record(1));root.chmod(0o755)
    before=store.trials();Store(root)
    assert stat.S_IMODE(root.stat().st_mode)==0o700
    assert store.trials()==before
