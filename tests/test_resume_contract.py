"""Resume guards before filesystem/runtime work."""
import json
from pathlib import Path

import pytest
import abl.engine as engine
from abl.models import Config, load_tasks
from abl.store import Store


@pytest.mark.parametrize('run_id',['../escaped','absolute','a/b','a'*31,'G'*32,''])
def test_bad_resume_id_cannot_create_a_lock(tmp_path,monkeypatch,run_id):
    if run_id == 'absolute':
        run_id = str(tmp_path/'absolute')
    monkeypatch.setattr(engine,'runtime_name',lambda _: 'unused')
    with pytest.raises(ValueError,match='Run ID'):
        engine.run_suite(tmp_path/'data',Config(),resume=run_id)
    assert not (tmp_path/'escaped.lock').exists()
    assert not (tmp_path/'data').exists()


def test_manifest_changes_with_task_bytes_and_order(tmp_path):
    folder=tmp_path/'task';folder.mkdir();(folder/'task.yaml').write_text('contract-one')
    task=load_tasks()['bugfix-rounding'][0]
    tasks={'first':(task,folder),'second':(task,folder)}
    initial=engine.corpus_manifest(tasks,['first','second'],'image-one')
    assert initial != engine.corpus_manifest(tasks,['second','first'],'image-one')
    assert initial != engine.corpus_manifest(tasks,['first','second'],'image-two')
    (folder/'task.yaml').write_text('contract-two')
    assert initial != engine.corpus_manifest(tasks,['first','second'],'image-one')


def test_store_adds_manifest_without_changing_legacy_rows(tmp_path):
    store=Store(tmp_path)
    config=Config().model_dump()
    store.create_run('a'*32,config)
    assert store.manifest('a'*32) is None
    manifest={'tasks':[],'image_id':'controlled'}
    store.create_run('b'*32,config,manifest=manifest)
    reopened=Store(tmp_path)
    assert reopened.run('a'*32)['config'] == config
    assert reopened.manifest('b'*32) == manifest


def test_changed_or_missing_manifest_blocks_resume_before_execution(tmp_path,monkeypatch):
    store=Store(tmp_path)
    config=Config(tasks=['bugfix-rounding'])
    store.create_run('a'*32,config.model_dump())
    monkeypatch.setattr(engine,'runtime_name',lambda _: 'unused')
    monkeypatch.setattr(engine,'image_identity',lambda *args:'controlled-image')
    with pytest.raises(ValueError,match='manifest'):
        engine.run_suite(tmp_path,config,resume='a'*32)
    store.create_run('b'*32,config.model_dump(),manifest={'tasks':[],'image_id':'old'})
    with pytest.raises(ValueError,match='changed'):
        engine.run_suite(tmp_path,config,resume='b'*32)
    assert store.trials() == []


def test_cli_rejects_bad_id_without_creating_store(tmp_path):
    from typer.testing import CliRunner
    from abl.cli import app
    root=tmp_path/'absent'
    result=CliRunner().invoke(app,['run','--root',str(root),'--resume','../escape'])
    assert result.exit_code==2 and 'Run ID' in result.output
    assert not root.exists()


def test_legacy_database_remains_compatible_after_additive_migration(tmp_path):
    import sqlite3
    db=sqlite3.connect(tmp_path/'results.sqlite3')
    db.execute('CREATE TABLE runs(id TEXT PRIMARY KEY,status TEXT,created_at TEXT,config TEXT,cancel INTEGER DEFAULT 0)')
    db.execute('CREATE TABLE trials(id TEXT PRIMARY KEY,run_id TEXT,slot INTEGER,data TEXT)')
    db.execute('INSERT INTO runs VALUES(?,?,?,?,0)',('a'*32,'COMPLETED','then','{}'));db.commit();db.close()
    store=Store(tmp_path);assert store.run('a'*32)['status']=='COMPLETED'
    # Downgrade remains valid: v1.0.1 reads/writes its original table shapes.
    db=sqlite3.connect(tmp_path/'results.sqlite3')
    db.execute('INSERT INTO runs VALUES(?,?,?,?,0)',('b'*32,'COMPLETED','later','{}'));db.commit();db.close()
    assert store.run('b'*32)['config']=={}


def test_manifest_framing_and_cache_do_not_change_contract(tmp_path):
    from abl.models import tree_hash
    (tmp_path/'a').write_text('bc');initial=tree_hash(tmp_path)
    (tmp_path/'a').unlink();(tmp_path/'ab').write_text('c')
    assert initial!=tree_hash(tmp_path)
    initial=tree_hash(tmp_path)
    cache=tmp_path/'__pycache__';cache.mkdir();(cache/'x.pyc').write_bytes(b'cache')
    assert initial==tree_hash(tmp_path)


def test_resume_lock_never_truncates_symlink_target(tmp_path,monkeypatch):
    victim=tmp_path/'evidence.txt';victim.write_text('retain evidence')
    root=tmp_path/'data';root.mkdir();(root/('a'*32+'.lock')).symlink_to(victim)
    monkeypatch.setattr(engine,'runtime_name',lambda _:'unused')
    monkeypatch.setattr(engine,'image_identity',lambda *args:'controlled-image')
    with pytest.raises((OSError,ValueError)):
        engine.run_suite(root,Config(),resume='a'*32)
    assert victim.read_text()=='retain evidence'
