"""Bounded opt-in live CLI checks. Never fabricates provider data.
Author: Ethan. Pass two explicit YAML configs and a fresh root.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import yaml

p=argparse.ArgumentParser(); p.add_argument('--config-a',type=Path,required=True); p.add_argument('--config-b',type=Path,required=True); p.add_argument('--root',type=Path,required=True); p.add_argument('--cli',default='abl'); a=p.parse_args()
a.root.mkdir(parents=True,exist_ok=True); results={}; records=[]
configs=[yaml.safe_load(path.read_text()) for path in (a.config_a,a.config_b)]
assert configs[0]!=configs[1], 'Two distinct configurations required'
assert all(c.get('provider')=='openrouter' and c.get('runner')=='agent' for c in configs)
assert all(c.get('spend_limit_usd',.25)<=.25 for c in configs), 'Live acceptance ceiling: $0.25 per run'
assert all(c.get('tasks')==['bugfix-rounding'] and c.get('repeats',1)==1 for c in configs)
if not all(os.environ.get(c.get('api_key_env','OPENROUTER_API_KEY')) for c in configs):
    results={f'BL-{i}':{'status':'BLOCKED_EXTERNAL','detail':'Missing live credential; Live model integration unverified'} for i in range(19,23)}
else:
    def execute(path):
        r=subprocess.run([a.cli,'run','--root',str(a.root),'--config',str(path)],capture_output=True,text=True,timeout=180)
        records.append({'command':['abl','run','--root',str(a.root),'--config',str(path)],'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        assert r.stdout.splitlines(), f'CLI returned no run ID (exit {r.returncode})'
        rid=json.loads(r.stdout.splitlines()[0])['run_id']
        inspect=subprocess.run([a.cli,'inspect',rid,'--root',str(a.root)],capture_output=True,text=True,check=True)
        return json.loads(inspect.stdout)['trials'][0]
    try:
        first=execute(a.config_a)
        assert first['status']=='PASS' and first['verifier']['exit_code']==0 and first['tool_calls']>0
        assert Path(first['artifact_dir'],'agent/workspace.tar').is_file()
        results['BL-19']={'status':'PASS','trial_id':first['id'],'detail':'Live tool calls produced artifacts accepted by independent behavioral verifier'}
        restricted=dict(configs[0],max_tool_steps=0,max_requests=1)
        path=a.root/'restricted.yaml'; path.write_text(yaml.safe_dump(restricted)); limited=execute(path)
        assert limited['status']=='FAIL' and limited['failure_category'] in ('step_limit','verification_failed','budget_limit')
        results['BL-20']={'status':'PASS','trial_id':limited['id'],'detail':'Restrictive live limit accurately classified incomplete outcome'}
        second=execute(a.config_b)
        assert second['status']=='PASS' and second['verifier']['exit_code']==0 and second['tool_calls']>0
        assert Path(second['artifact_dir'],'agent/workspace.tar').is_file()
        assert (first['ttft_seconds'] is not None)==bool(configs[0].get('streaming'))
        assert (second['ttft_seconds'] is not None)==bool(configs[1].get('streaming'))
        assert first['id']!=second['id'] and first['fixture_hash']==second['fixture_hash'] and first['config_hash']!=second['config_hash']
        r=subprocess.run([a.cli,'compare','--root',str(a.root)],capture_output=True,text=True,check=True)
        assert len(json.loads(r.stdout)['groups'])>=2
        results['BL-21']={'status':'PASS','trial_ids':[first['id'],second['id']],'detail':'Distinct live configurations use identical fixture hash and independent records'}
        for t in (first,limited,second):
            assert not t.get('request_pending') and not t.get('cleanup_errors')
            assert t['cost_usd'] is not None and t['cost_usd']>=0
            trace=[json.loads(x) for x in Path(t['artifact_dir'],'trace.jsonl').read_text().splitlines()]
            responses=[x for x in trace if x['kind']=='provider']; assert responses
            for field,key in [('input_tokens','prompt_tokens'),('output_tokens','completion_tokens')]:
                values=[(x.get('usage') or {}).get(key) for x in responses]
                expected=sum(values) if all(v is not None for v in values) else None
                assert t[field]==expected,(field,t[field],expected)
            cached=[((x.get('usage') or {}).get('prompt_tokens_details') or {}).get('cached_tokens') for x in responses]
            assert t['cached_input_tokens']==(sum(cached) if all(v is not None for v in cached) else None)
            costs=[(x.get('usage') or {}).get('cost') for x in responses]
            if all(v is not None for v in costs): assert t['cost_usd']==sum(costs) and t['cost_source']=='provider.usage.cost'
        results['BL-22']={'status':'PASS','detail':'Persisted totals exactly match actual returned usage; missing token metadata remains null'}
    except Exception as e:
        results['failure']={'status':'FAIL','detail':repr(e)}
(a.root/'live-acceptance.json').write_text(json.dumps({'scenarios':results,'commands':records},indent=2))
print(json.dumps(results,indent=2))
sys.exit(1 if 'failure' in results else 2 if any(x['status']=='BLOCKED_EXTERNAL' for x in results.values()) else 0)
