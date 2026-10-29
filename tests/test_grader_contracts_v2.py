"""Pure schema/property checks. Candidate execution belongs to grader_v2_e2e."""
from pathlib import Path
import importlib.util
import json

import pytest
from hypothesis import given, strategies as st
from abl.models import load_tasks, tree_hash

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('grader_support',ROOT/'corpus/multistep-ledger/verifier/support.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_all_changed_contracts_have_new_versions_and_archived_bytes():
    tasks=load_tasks();assert len(tasks)==12
    for tid,(task,folder) in tasks.items():
        assert task.version=='2.0'
        old=ROOT/'corpus_history/2026-10-27'/tid
        assert old.is_dir()
        assert tree_hash(folder)!=tree_hash(old)
        assert 'support.py' in {p.name for p in (folder/'verifier').iterdir()}


@given(number=st.integers(min_value=-10**6,max_value=10**6))
def test_integer_schema_rejects_equal_float_nested_in_output(number):
    with pytest.raises(AssertionError): module.equal({'rows':[{'cents':float(number)}]}, {'rows':[{'cents':number}]})


@pytest.mark.parametrize('wrong',[True,False,None,'0',[],{}])
def test_integer_schema_rejects_other_types(wrong):
    with pytest.raises(AssertionError):module.equal({'count':wrong},{'count':0})


def test_unique_and_sorted_key_requirements():
    with pytest.raises(AssertionError):module.load('{"a":1,"a":1}')
    with pytest.raises(AssertionError):module.sorted_json('{"b":1,"a":2}')
    with pytest.raises(AssertionError):module.sorted_json('{"a":{"z":1,"b":2}}')
    assert module.sorted_json('{"a": {"b":2, "z":1}}')=={'a':{'b':2,'z':1}}


@pytest.mark.parametrize('tid',['navigation-config','navigation-routes'])
def test_navigation_reference_has_structured_explanation_and_rejects_contradiction(tid):
    actions=json.loads((ROOT/'corpus'/tid/'reference.json').read_text())
    answer=json.loads(next(a['arguments']['content'] for a in actions if a['tool']=='write_file'))
    assert isinstance(answer['explanation'],dict)
    wrong=json.loads(json.dumps(answer));key=next(iter(wrong['explanation']))
    wrong['explanation'][key]['value' if tid.endswith('config') else 'methods']='wrong'
    with pytest.raises(AssertionError):module.equal(wrong,answer)
    module.equal(json.loads(json.dumps(answer,sort_keys=True,indent=4)),answer)
