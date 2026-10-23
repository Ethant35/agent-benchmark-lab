"""Control-flow fault injection; real container cleanup is a separate E2E gate."""
import pytest
from abl.engine import Execution
from abl.models import Config, load_tasks
from abl.store import Store


def test_artifact_persistence_failure_cannot_prevent_cleanup(tmp_path,monkeypatch):
    store=Store(tmp_path)
    config=Config()
    rid='a'*32
    store.create_run(rid,config.model_dump())
    run=Execution(store,rid,0,*load_tasks()['bugfix-rounding'],config,'unused')
    cleaned=[]
    def setup(_): raise RuntimeError('Controlled setup failure')
    def disk_full(*args,**kwargs): raise OSError('Controlled full results disk')
    monkeypatch.setattr(run.box,'start',setup)
    monkeypatch.setattr(run.box,'raw',lambda *args,**kwargs:b'')
    monkeypatch.setattr(run.box,'snapshot',lambda *args:None)
    monkeypatch.setattr(run.box,'cleanup',lambda:cleaned.append(True) or [])
    run.box.artifact={'status':'error'}
    monkeypatch.setattr(run,'event',disk_full)
    with pytest.raises(OSError,match='full results disk'): run.execute()
    assert cleaned == [True]
